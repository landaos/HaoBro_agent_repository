# ============================================
# exception_handler.py - 全局异常处理 + 统一错误响应（生产级）
# ============================================
"""
统一异常处理体系，确保所有 API 响应格式一致。

错误响应格式：
{
    "error_code": "NOT_FOUND",
    "message": "会话不存在",
    "detail": null
}

使用方式：
    # 在路由中抛出业务异常
    raise NotFoundException("会话不存在")

    # 保持原有 HTTPException 也兼容（自动转换）
    raise HTTPException(status_code=404, detail="会话不存在")

    # 在 main.py 中注册
    from src.middleware.exception_handler import register_exception_handlers
    register_exception_handlers(app)
"""
import traceback
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.logger.logger import logger


# ═══════════════════════════════════════════════════════════
# 错误响应模型
# ═══════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """统一错误响应体"""
    error_code: str
    message: str
    detail: Any = None


# ═══════════════════════════════════════════════════════════
# 错误码常量
# ═══════════════════════════════════════════════════════════

class ErrorCode:
    """业务错误码（与 HTTP 状态码解耦，前端可据此做国际化）"""
    # 通用
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    # 业务
    LLM_ERROR = "LLM_ERROR"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    DOCUMENT_ERROR = "DOCUMENT_ERROR"
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    SESSION_EXPIRED = "SESSION_EXPIRED"


# ═══════════════════════════════════════════════════════════
# 业务异常类
# ═══════════════════════════════════════════════════════════

class AppException(Exception):
    """应用基类异常

    Attributes:
        error_code: 业务错误码（见 ErrorCode）
        message: 用户可读的错误描述
        status_code: HTTP 状态码
        detail: 额外的调试信息（生产环境建议为 None）
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        detail: Any = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundException(AppException):
    """资源不存在 (404)"""
    def __init__(self, message: str = "资源不存在", detail: Any = None):
        super().__init__(ErrorCode.NOT_FOUND, message, 404, detail)


class UnauthorizedException(AppException):
    """未认证 (401)"""
    def __init__(self, message: str = "未登录或登录已过期", detail: Any = None):
        super().__init__(ErrorCode.UNAUTHORIZED, message, 401, detail)


class ForbiddenException(AppException):
    """无权限 (403)"""
    def __init__(self, message: str = "无权限访问", detail: Any = None):
        super().__init__(ErrorCode.FORBIDDEN, message, 403, detail)


class ConflictException(AppException):
    """资源冲突 (409)"""
    def __init__(self, message: str = "资源冲突", detail: Any = None):
        super().__init__(ErrorCode.CONFLICT, message, 409, detail)


class ValidationException(AppException):
    """参数校验失败 (422)"""
    def __init__(self, message: str = "参数校验失败", detail: Any = None):
        super().__init__(ErrorCode.INVALID_INPUT, message, 422, detail)


class RateLimitException(AppException):
    """请求过频繁 (429)"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试", detail: Any = None):
        super().__init__(ErrorCode.RATE_LIMITED, message, 429, detail)


class LLMException(AppException):
    """LLM 调用失败 (502)"""
    def __init__(self, message: str = "AI 服务暂时不可用", detail: Any = None):
        super().__init__(ErrorCode.LLM_ERROR, message, 502, detail)


class EmbeddingException(AppException):
    """向量化失败 (502)"""
    def __init__(self, message: str = "文档处理服务暂时不可用", detail: Any = None):
        super().__init__(ErrorCode.EMBEDDING_ERROR, message, 502, detail)


class DocumentException(AppException):
    """文档处理失败 (400)"""
    def __init__(self, message: str = "文档处理失败", detail: Any = None):
        super().__init__(ErrorCode.DOCUMENT_ERROR, message, 400, detail)


class FileTooLargeException(AppException):
    """文件过大 (413)"""
    def __init__(self, message: str = "文件大小超出限制", detail: Any = None):
        super().__init__(ErrorCode.FILE_TOO_LARGE, message, 413, detail)


class UnsupportedFileTypeException(AppException):
    """不支持的文件类型 (415)"""
    def __init__(self, message: str = "不支持的文件类型", detail: Any = None):
        super().__init__(ErrorCode.UNSUPPORTED_FILE_TYPE, message, 415, detail)


# ═══════════════════════════════════════════════════════════
# 异常处理器
# ═══════════════════════════════════════════════════════════

def _build_response(
    error_code: str,
    message: str,
    status_code: int,
    detail: Any = None,
) -> JSONResponse:
    """构建统一错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            detail=detail,
        ).model_dump(),
    )


async def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理 AppException 及其子类"""
    logger.warning(
        f"【异常】{exc.error_code} | {exc.message}"
        f" | path={request.url.path} | method={request.method}"
    )
    return _build_response(exc.error_code, exc.message, exc.status_code, exc.detail)


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理 HTTPException（兼容原有代码，自动映射 error_code）"""
    status_to_code = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        413: ErrorCode.FILE_TOO_LARGE,
        415: ErrorCode.UNSUPPORTED_FILE_TYPE,
        429: ErrorCode.RATE_LIMITED,
    }
    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    if exc.status_code >= 500:
        logger.error(
            f"【异常】HTTP {exc.status_code} | {exc.detail}"
            f" | path={request.url.path} | method={request.method}"
        )
    else:
        logger.warning(
            f"【异常】HTTP {exc.status_code} | {exc.detail}"
            f" | path={request.url.path} | method={request.method}"
        )

    return _build_response(
        error_code=error_code,
        message=str(exc.detail) if exc.detail else "请求失败",
        status_code=exc.status_code,
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理 Pydantic 校验失败（422），返回结构化的字段错误"""
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"【异常】校验失败 | {len(field_errors)} fields"
        f" | path={request.url.path} | method={request.method}"
    )

    return _build_response(
        error_code=ErrorCode.INVALID_INPUT,
        message="请求参数校验失败",
        status_code=422,
        detail=field_errors if len(field_errors) <= 5 else field_errors[:5],
    )


async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常（500）

    安全原则：
      - 不向客户端暴露异常信息和堆栈
      - 完整异常栈写入日志
      - 返回统一格式的 500 响应
    """
    # 获取请求 ID（由 LoggingMiddleware 注入）
    request_id = getattr(request.state, "request_id", None) or "unknown"

    # 记录完整异常栈
    logger.error(
        f"【异常】未捕获异常 | {type(exc).__name__}: {exc}"
        f" | path={request.url.path} | method={request.method}"
        f" | req_id={request_id}"
    )
    logger.error(f"【异常】堆栈跟踪:\n{traceback.format_exc()}")

    return _build_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="服务器内部错误，请稍后重试",
        status_code=500,
    )


# ═══════════════════════════════════════════════════════════
# 注册函数
# ═══════════════════════════════════════════════════════════

def register_exception_handlers(app: FastAPI) -> None:
    """注册所有全局异常处理器到 FastAPI 应用

    Usage:
        from src.middleware.exception_handler import register_exception_handlers
        register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, _app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _global_exception_handler)

    logger.info("【中间件】全局异常处理器已注册")