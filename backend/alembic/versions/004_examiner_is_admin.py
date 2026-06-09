"""Add is_admin flag for examiner users.

Revision ID: 004_examiner_is_admin
Revises: 003_seed_platform_settings
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_examiner_is_admin"
down_revision: Union[str, None] = "003_seed_platform_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
    )
    op.execute(
        """
        UPDATE users
        SET is_admin = true
        WHERE user_id = (
            SELECT user_id
            FROM users
            WHERE role = 'EXAMINER' AND deleted_at IS NULL
            ORDER BY created_at ASC
            LIMIT 1
        )
        """
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
