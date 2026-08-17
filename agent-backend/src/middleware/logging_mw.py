# ============================================
# logging_mw.py - 请求日志中间件（生产级）
# ============================================
"""
记录每个 HTTP 请求的关键信息：方法、路径、状态码、耗时、用户、请求 ID。

日志格式（单行，便于 grep/ELK 解析）：
  [req_id] POST /api/v1/chat | 200 | 1.23s | user=xxx | ip=1.2.3.4

特性：
  - 自动生成 X-Request-ID（透传或新建），注入响应头
  - 从 JWT 轻量提取 user_id（仅解码，不查 DB）
  - 跳过健康检查 / 文档页，避免日志噪音
  - 慢请求告警（> 3s）
  - 4xx/5xx 自动升级为 WARNING/ERROR 级别
"""
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.logger.logger import logger

# ── 慢请求阈值（秒） ──
SLOW_REQUEST_THRESHOLD = 3.0

# ── 跳过日志的路径前缀（健康检查、静态资源、文档） ──
SKIP_LOG_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
)

# ── 请求 ID 头名称 ──
REQUEST_ID_HEADER = "X-Request-ID"


def _extract_user_id(request: Request) -> Optional[str]:
    """从 Authorization header 轻量提取 user_id（仅 JWT 解码，不查 DB）

    如果解码失败，返回 None（不阻塞请求）。
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        from jose import jwt  # noqa: PLC0415
        from src.config import settings  # noqa: PLC0415

        token = auth_header[7:]
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},  # 不验证过期（仅取 user_id，不拦截请求）
        )
        return payload.get("user_id")
    except Exception:
        return None


def _should_skip(path: str) -> bool:
    """判断是否跳过日志记录"""
    return path.startswith(SKIP_LOG_PREFIXES)


class LoggingMiddleware(BaseHTTPMiddleware):
    """生产级请求日志中间件

    在 main.py 中注册：
        from src.middleware.logging_mw import LoggingMiddleware
        app.add_middleware(LoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── 跳过无需记录的路径 ──
        if _should_skip(request.url.path):
            return await call_next(request)

        # ── 请求 ID ──
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        # ── 用户信息 ──
        user_id = _extract_user_id(request)

        # ── 客户端 IP ──
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        # ── 计时开始 ──
        start_time = time.monotonic()

        # ── 执行请求 ──
        response = await call_next(request)

        # ── 计算耗时 ──
        duration_ms = (time.monotonic() - start_time) * 1000
        duration_s = duration_ms / 1000

        # ── 注入响应头 ──
        response.headers[REQUEST_ID_HEADER] = request_id

        # ── 构造日志消息 ──
        user_part = f" 用户={user_id}" if user_id else ""
        ip_part = f" IP={client_ip}"

        log_msg = (
            f"请求ID={request_id} 方法={request.method} 路径={request.url.path}"
            f" 状态码={response.status_code}"
            f" 耗时={duration_s:.2f}s"
            f"{user_part}{ip_part}"
        )

        # ── 按状态码分级日志 ──
        if response.status_code >= 500:
            logger.error(f"【请求】{log_msg}")
        elif response.status_code >= 400:
            logger.warning(f"【请求】{log_msg}")
        elif duration_s > SLOW_REQUEST_THRESHOLD:
            logger.warning(f"【请求】慢请求（>{SLOW_REQUEST_THRESHOLD}s）| {log_msg}")
        else:
            logger.info(f"【请求】{log_msg}")

        return response