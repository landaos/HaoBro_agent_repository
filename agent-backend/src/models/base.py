"""SQLAlchemy 声明基类 + 公共 Mixin"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UUIDMixin:
     """UUID 主键"""

     id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: uuid4().hex, # 32 位 hex 串，比 UUID 类型更快
    )


class TimeMixin:
    """创建时间 + 更新时间"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )
