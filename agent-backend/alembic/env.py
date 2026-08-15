"""Alembic 迁移环境配置"""

import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config

# 将项目根目录加入 sys.path，确保能 import src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import settings
from src.models import Base

# 导入所有模型（必须，否则 alembic --autogenerate 检测不到新表）
import src.models  # noqa: F811, E402 — 确保模型注册到 Base.metadata

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL 脚本，不连数据库"""
    context.configure(
        url=settings.db_url_sync,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：直接连数据库执行迁移"""
    connectable = engine_from_config(
        {"sqlalchemy.url": settings.db_url_sync},
        prefix="sqlalchemy.",
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
