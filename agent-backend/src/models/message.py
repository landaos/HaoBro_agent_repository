"""消息表 — messages"""

from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimeMixin, UUIDMixin


class Message(UUIDMixin, TimeMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属会话 ID",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="user | assistant | system | tool",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="消息内容"
    )
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="额外元数据，如用户反馈、评分等",
    )

    # 多对一关联
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_created_at", "created_at"),
    )
