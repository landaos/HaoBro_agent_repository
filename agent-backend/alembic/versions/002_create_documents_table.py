"""建表：documents + document_chunks（含 pgvector 扩展）

Revision ID: 002
Revises: 08c0e1edfdc8
Create Date: 2026-07-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# 必须与 DashScope text-embedding-v3 输出维度一致
EMBEDDING_DIM = 1024

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. 扩展（需超级用户权限，已存在则跳过） ──
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── 2. documents 表 ──
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kb_id", sa.Integer(), nullable=False, comment="知识库 ID"),
        sa.Column("title", sa.String(512), nullable=False, comment="文档标题"),
        sa.Column("file_name", sa.String(512), nullable=False, comment="原始文件名"),
        sa.Column("file_path", sa.String(1024), nullable=True, comment="存储路径"),
        sa.Column("file_size", sa.BigInteger(), nullable=True, comment="文件大小(字节)"),
        sa.Column("file_type", sa.String(10), nullable=False, comment="pdf / txt / md"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending | processing | completed | failed",
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0", comment="分块数量"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_doc_kb_id", "documents", ["kb_id"])
    op.create_index("idx_doc_status", "documents", ["status"])

    # ── 3. document_chunks 向量表 ──
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id          BIGSERIAL PRIMARY KEY,
            doc_id      INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            kb_id       INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content     TEXT NOT NULL,
            embedding   vector({EMBEDDING_DIM}),
            metadata    JSONB DEFAULT '{{}}',
            created_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunk_doc_id ON document_chunks(doc_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunk_kb_id ON document_chunks(kb_id);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
        f"ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm "
        "ON document_chunks USING gin (content gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv "
        "ON document_chunks USING gin (to_tsvector('english', content));"
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
