"""创建知识库表 + 添加外键到 documents

Revision ID: 004
Revises: 003
Create Date: 2026-07-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. 创建知识库表 ──
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户 ID"),
        sa.Column("name", sa.String(255), nullable=False, comment="知识库名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
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
    op.create_index("idx_kb_user_id", "knowledge_bases", ["user_id"])

    # ── 2. documents.kb_id 加上外键 ──
    op.execute("""
        ALTER TABLE documents
        ADD CONSTRAINT fk_doc_kb_id
        FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
        ON DELETE CASCADE
        NOT VALID;
    """)
    op.execute("ALTER TABLE documents VALIDATE CONSTRAINT fk_doc_kb_id;")


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS fk_doc_kb_id;")
    op.drop_table("knowledge_bases")
