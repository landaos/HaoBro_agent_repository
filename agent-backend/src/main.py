"""
应用入口

HF_ENDPOINT 必须在任何导入之前设置，确保 huggingface_hub
在首次 import 前就能读到国内镜像地址。
"""
import os
import logging

# ── 强制使用 Hugging Face 国内镜像（必须在 huggingface_hub 首次导入前设置） ──
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# ── 降级 SQLAlchemy 连接池的 "Exception terminating connection" 日志 ──
# 客户端断开 SSE 流时，Starlette 取消请求任务，连接池清理被中断会打印此日志。
# pool_pre_ping=True 已确保后续请求拿到健康连接，此日志仅为噪音，降级为 WARNING。
logging.getLogger("sqlalchemy.pool.impl.AsyncAdaptedQueuePool").setLevel(logging.WARNING)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    health,
    chat,
    conversations,
    users,
    knowledge_bases,
    documents,
)
from src.config import settings
from src.db.session import init_db, close_db
from src.logger.logger import logger
from src.middleware.logging_mw import LoggingMiddleware
from src.middleware.exception_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理"""
    logger.info(f"【app】应用启动 - HF_ENDPOINT={os.environ.get('HF_ENDPOINT', '未设置')}")
    await init_db()
    _prewarm()
    yield
    await close_db()
    logger.info("【app】应用关闭")


def _prewarm() -> None:
    """启动时加载轻量组件，避免用户首次使用时等待"""
    try:
        from langchain_community.document_loaders import PyMuPDFLoader  # noqa: F401
        logger.info("【app】文档加载器预热就绪（PyMuPDFLoader）")
    except Exception as e:
        logger.warning(f"【app】文档加载器预热失败: {e}")


app = FastAPI(
    title="Agent Backend - 企业内部知识库问答助手",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS（允许前端跨域调用） ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 请求日志中间件 ──
app.add_middleware(LoggingMiddleware)

# ── 全局异常处理器 ──
register_exception_handlers(app)

# ── 注册路由 ──
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["对话"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["会话管理"])
app.include_router(users.user_router, prefix="/api/v1", tags=["用户管理"])
app.include_router(knowledge_bases.router, prefix="/api/v1/knowledge-bases", tags=["知识库管理"])
app.include_router(documents.router, prefix="/api/v1/knowledge-bases", tags=["文档管理"])
