"""精简 documents 和 document_chunks 表，删除多余字段

changes:
  - documents: 删除 error_message, vector_ids, checksum, metadata, uploader_id
  - document_chunks: 删除 token_count, headings, page_numbers, chunk_type

Revision ID: 003
Revises: 002
Create Date: 2026-07-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── documents 表：删除多余字段 ──
    op.drop_column("documents", "error_message")
    op.drop_column("documents", "vector_ids")
    op.drop_column("documents", "checksum")
    op.drop_column("documents", "metadata")
    op.drop_column("documents", "uploader_id")

    # ── document_chunks 表：删除多余字段 ──
    op.drop_column("document_chunks", "token_count")
    op.drop_column("document_chunks", "headings")
    op.drop_column("document_chunks", "page_numbers")
    op.drop_column("document_chunks", "chunk_type")

    # ── 删除废弃索引（if_exists 兼容已不存在的索引） ──
    op.execute("DROP INDEX IF EXISTS idx_doc_uploader_id;")
    op.execute("DROP INDEX IF EXISTS idx_doc_kb_status;")
    op.execute("DROP INDEX IF EXISTS idx_doc_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_chunk_type;")


def downgrade() -> None:
    # ── documents：加回字段 ──
    op.add_column("documents", sa.Column("uploader_id", sa.Integer(), nullable=False, comment="上传者用户 ID"))
    op.add_column("documents", sa.Column("metadata", postgresql.JSONB(), nullable=True, comment="自定义元数据"))
    op.add_column("documents", sa.Column("checksum", sa.String(64), nullable=True, comment="文件 SHA256"))
    op.add_column("documents", sa.Column("vector_ids", postgresql.JSONB(), nullable=True, comment="向量数据库中对应的 ID 列表"))
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True, comment="处理失败时的错误信息"))

    # ── document_chunks：加回字段 ──
    op.add_column("document_chunks", sa.Column("chunk_type", sa.String(50), nullable=True))
    op.add_column("document_chunks", sa.Column("page_numbers", postgresql.ARRAY(sa.Integer()), nullable=True))
    op.add_column("document_chunks", sa.Column("headings", postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column("document_chunks", sa.Column("token_count", sa.Integer(), nullable=True))

    # ── 加回索引 ──
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON document_chunks(chunk_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_doc_created_at ON documents(created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_doc_kb_status ON documents(kb_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_doc_uploader_id ON documents(uploader_id);")
