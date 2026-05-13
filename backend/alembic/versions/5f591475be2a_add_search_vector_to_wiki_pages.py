"""add search_vector to wiki_pages

Revision ID: 5f591475be2a
Revises: a625e95516e3
Create Date: 2026-05-14 01:04:02.467380

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f591475be2a"
down_revision: str | None = "a625e95516e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("wiki_pages", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))
    op.execute(
        "UPDATE wiki_pages SET search_vector = to_tsvector('simple', COALESCE(title,'') || ' ' || COALESCE(content,''))"
    )
    op.create_index("ix_wiki_pages_search_vector", "wiki_pages", ["search_vector"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_wiki_pages_search_vector", table_name="wiki_pages")
    op.drop_column("wiki_pages", "search_vector")
