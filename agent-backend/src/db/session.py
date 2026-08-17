"""PostgreSQL 异步数据库会话

三步搞定：
  1. 创建异步引擎（连接池）
  2. 创建 session 工厂
  3. 提供 get_session 依赖注入

使用方式：
  async with async_session_factory() as session:
      result = await session.execute(...)
"""

from collections.abc import AsyncGenerator

from src.logger.logger import logger
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from src.config import settings

# ============================================================
# 第一步：创建异步引擎
# ============================================================
# 引擎 = 数据库连接池，负责管理和复用数据库连接。
# asyncpg 是 PostgreSQL 的异步驱动，比 psycopg2 快 2-3 倍。
#
# 参数说明：
#   echo=True       → 打印所有 SQL 语句（开发调试用，生产关掉）
#   pool_size=10    → 连接池大小（同时最多 10 个连接）
#   max_overflow=20 → 连接池用满后最多再临时开 20 个（峰值时）
#                     总连接上限 = pool_size + max_overflow = 30
#   pool_pre_ping=True → 每次从连接池拿连接前先 ping 一下，
#                         确保连接没断（生产环境推荐开启）
# ============================================================
engine = create_async_engine(
    settings.db_url,
    echo=False,  # 关闭 SQL 日志，避免刷屏
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # 借出前 ping 连接，丢弃已断开/损坏连接
    pool_recycle=300,      # 5分钟强制回收连接，避免 idle 残留
)

# ============================================================
# 第二步：创建 session 工厂
# ============================================================
# session = 工作的基本单位，增删改查都通过 session 做。
# async_sessionmaker 是工厂函数，每次调用() 创建一个新 session。
#
# expire_on_commit=False → commit 后对象不过期，还能接着用
# （默认 True 的话，commit 后所有属性变 expired，下次访问会重新查库）
# ============================================================
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入函数，返回异步数据库会话

    注意：各 service 函数自己负责 commit，此处不再自动提交，
    避免与 service 层产生双重提交导致数据不一致。
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================
# 第三步：生命周期管理
# ============================================================
async def init_db():
    """应用启动时调用：连接验证 + 建表 + 建扩展索引"""
    from src.models import Base
    from sqlalchemy import text

    # 1. 建所有 ORM 表（documents, conversations, messages 等）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"【db】ORM 表已就绪 | {settings.db_host}:{settings.db_port}/{settings.db_name}")

    # 2. 启用 pgvector 扩展（向量存储需要）
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    logger.info("【db】pgvector 扩展已启用")


async def close_db():
    """应用关闭时调用，释放连接池"""
    await engine.dispose()
    print("[DB] 连接池已释放")
