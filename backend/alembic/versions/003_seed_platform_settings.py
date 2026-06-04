"""Seed default platform settings.

Revision ID: 003_seed_platform_settings
Revises: 002_audit_schema
Create Date: 2026-06-04

"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_seed_platform_settings"
down_revision: Union[str, None] = "002_audit_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO platform_settings (setting_key, setting_value) VALUES
            ('retention_days_completed', '730'::jsonb),
            ('allow_examinee_retake', 'false'::jsonb),
            ('question_selection_mode', '"FIXED_ORDER"'::jsonb)
        ON CONFLICT (setting_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM platform_settings
        WHERE setting_key IN (
            'retention_days_completed',
            'allow_examinee_retake',
            'question_selection_mode'
        )
        """
    )
