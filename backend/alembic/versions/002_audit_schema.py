"""Audit schema and audit_logs table.

Revision ID: 002_audit_schema
Revises: 001_initial_app
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_audit_schema"
down_revision: Union[str, None] = "001_initial_app"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

audit_outcome = postgresql.ENUM("success", "failure", name="audit_outcome", create_type=False)


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    bind = op.get_bind()
    audit_outcome.create(bind, checkfirst=True)

    op.create_table(
        "audit_logs",
        sa.Column(
            "log_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", audit_outcome, nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("log_id"),
        schema="audit",
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        [sa.text("created_at DESC")],
        unique=False,
        schema="audit",
    )
    op.create_index(
        "ix_audit_logs_actor_id_created_at",
        "audit_logs",
        ["actor_id", "created_at"],
        unique=False,
        schema="audit",
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id_created_at", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs", schema="audit")
    op.drop_table("audit_logs", schema="audit")
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE")

    bind = op.get_bind()
    audit_outcome.drop(bind, checkfirst=True)
