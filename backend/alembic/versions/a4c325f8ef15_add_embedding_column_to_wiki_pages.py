"""add embedding column to wiki_pages

Revision ID: a4c325f8ef15
Revises: 5f591475be2a
Create Date: 2026-05-14 01:13:50.191464

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4c325f8ef15"
down_revision: str | None = "5f591475be2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("wiki_pages", sa.Column("embedding", Vector(1536), nullable=True))


def downgrade() -> None:
    op.drop_column("wiki_pages", "embedding")
