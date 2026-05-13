"""add user_id to knowledge_bases

Revision ID: b3f490847caf
Revises: a4c325f8ef15
Create Date: 2026-05-14 01:25:07.374189

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f490847caf"
down_revision: str | None = "a4c325f8ef15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("knowledge_bases", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_bases_user_id", "knowledge_bases", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_knowledge_bases_user_id", "knowledge_bases", type_="foreignkey")
    op.drop_column("knowledge_bases", "user_id")
