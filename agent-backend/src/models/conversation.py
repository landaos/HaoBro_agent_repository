"""会话表 — conversations"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimeMixin, UUIDMixin


class Conversation(UUIDMixin, TimeMixin, Base):
    __tablename__ = "conversations"

    session_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="客户端传入的会话 ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="用户 ID"
    )
    title: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="自动生成的会话标题"
    )

    # 一对多关联（Message 通过 FK 关联）
    # cascade="all, delete-orphan" 确保删除会话时同时删除所有消息
    # （数据库层另有 ON DELETE CASCADE 作为兜底）
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_created_at", "created_at"),
    )
