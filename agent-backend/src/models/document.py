"""文档 ORM 模型"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimeMixin


class Document(TimeMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True, comment="知识库 ID"
    )
    title: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="文档标题"
    )
    file_name: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="原始文件名"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="存储路径"
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="文件大小(字节)"
    )
    file_type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="文件类型: pdf/txt/md"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending | processing | completed | failed"
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="分块数量"
    )

    # 反向关联知识库
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase", back_populates="documents"
    )

    __table_args__ = (
        Index("idx_doc_kb_id", "kb_id"),
        Index("idx_doc_status", "status"),
    )
