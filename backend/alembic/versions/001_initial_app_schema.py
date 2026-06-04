"""Initial application schema per docs/MCQ_Platform_ERD.md.

Revision ID: 001_initial_app
Revises:
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_app"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("EXAMINER", "EXAMINEE", name="user_role", create_type=False)
correct_option = postgresql.ENUM("A", "B", "C", "D", name="correct_option", create_type=False)
session_status = postgresql.ENUM(
    "ACTIVE", "COMPLETED", "EXPIRED", name="session_status", create_type=False
)
selection_mode = postgresql.ENUM(
    "FIXED_ORDER", "RANDOM_SAMPLE", name="selection_mode", create_type=False
)
selected_option = postgresql.ENUM("A", "B", "C", "D", name="selected_option", create_type=False)
erasure_job_status = postgresql.ENUM(
    "PENDING", "COMPLETED", "FAILED", name="erasure_job_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    correct_option.create(bind, checkfirst=True)
    session_status.create(bind, checkfirst=True)
    selection_mode.create(bind, checkfirst=True)
    selected_option.create(bind, checkfirst=True)
    erasure_job_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("prn_ciphertext", sa.Text(), nullable=True),
        sa.Column("prn_lookup_hash", sa.String(length=64), nullable=True),
        sa.Column("name_ciphertext", sa.Text(), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("privacy_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(role = 'EXAMINER' AND username IS NOT NULL AND password_hash IS NOT NULL "
            "AND prn_ciphertext IS NULL AND prn_lookup_hash IS NULL AND name_ciphertext IS NULL) "
            "OR (role = 'EXAMINEE' AND username IS NULL AND password_hash IS NULL "
            "AND prn_ciphertext IS NOT NULL AND prn_lookup_hash IS NOT NULL "
            "AND name_ciphertext IS NOT NULL)",
            name="ck_users_role_fields",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_users_username_examiner
        ON users (username)
        WHERE role = 'EXAMINER' AND username IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_users_prn_examinee_active
        ON users (prn_lookup_hash)
        WHERE role = 'EXAMINEE' AND deleted_at IS NULL
        """
    )

    op.create_table(
        "questions",
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("option_a", sa.Text(), nullable=False),
        sa.Column("option_b", sa.Text(), nullable=False),
        sa.Column("option_c", sa.Text(), nullable=False),
        sa.Column("option_d", sa.Text(), nullable=False),
        sa.Column("correct_option", correct_option, nullable=False),
        sa.Column("question_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("char_length(question_text) <= 2000", name="ck_questions_text_len"),
        sa.CheckConstraint("char_length(option_a) <= 500", name="ck_questions_option_a_len"),
        sa.CheckConstraint("char_length(option_b) <= 500", name="ck_questions_option_b_len"),
        sa.CheckConstraint("char_length(option_c) <= 500", name="ck_questions_option_c_len"),
        sa.CheckConstraint("char_length(option_d) <= 500", name="ck_questions_option_d_len"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("question_id"),
    )
    op.create_index(
        "ix_questions_is_deleted_question_id",
        "questions",
        ["is_deleted", "question_id"],
        unique=False,
    )

    op.create_table(
        "question_versions",
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("option_a", sa.String(length=500), nullable=False),
        sa.Column("option_b", sa.String(length=500), nullable=False),
        sa.Column("option_c", sa.String(length=500), nullable=False),
        sa.Column("option_d", sa.String(length=500), nullable=False),
        sa.Column("correct_option", correct_option, nullable=False),
        sa.Column("modified_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(question_text) <= 2000",
            name="ck_question_versions_text_len",
        ),
        sa.ForeignKeyConstraint(["modified_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"]),
        sa.PrimaryKeyConstraint("version_id"),
        sa.UniqueConstraint(
            "question_id", "version_number", name="uq_question_versions_question_version"
        ),
    )

    op.create_table(
        "test_sessions",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", session_status, nullable=False),
        sa.Column("selection_mode", selection_mode, nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_test_sessions_user_id_status",
        "test_sessions",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_test_sessions_status_last_activity_at",
        "test_sessions",
        ["status", "last_activity_at"],
        unique=False,
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_test_sessions_one_active_per_user
        ON test_sessions (user_id)
        WHERE status = 'ACTIVE'
        """
    )

    op.create_table(
        "session_questions",
        sa.Column(
            "session_question_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("question_version_snapshot", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 1 AND position <= 50", name="ck_session_questions_position"
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["test_sessions.session_id"]),
        sa.PrimaryKeyConstraint("session_question_id"),
        sa.UniqueConstraint("session_id", "position", name="uq_session_questions_session_position"),
        sa.UniqueConstraint(
            "session_id", "question_id", name="uq_session_questions_session_question"
        ),
    )

    op.create_table(
        "responses",
        sa.Column(
            "response_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_option", selected_option, nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"]),
        sa.ForeignKeyConstraint(["session_id"], ["test_sessions.session_id"]),
        sa.PrimaryKeyConstraint("response_id"),
        sa.UniqueConstraint("session_id", "question_id", name="uq_responses_session_question"),
    )

    op.create_table(
        "platform_settings",
        sa.Column("setting_key", sa.String(length=128), nullable=False),
        sa.Column("setting_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("setting_key"),
    )

    op.create_table(
        "erasure_jobs",
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("examinee_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", erasure_job_status, nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["examinee_user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["operator_user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("job_id"),
    )


def downgrade() -> None:
    op.drop_table("erasure_jobs")
    op.drop_table("platform_settings")
    op.drop_table("responses")
    op.drop_table("session_questions")
    op.execute("DROP INDEX IF EXISTS uq_test_sessions_one_active_per_user")
    op.drop_table("test_sessions")
    op.drop_table("question_versions")
    op.drop_index("ix_questions_is_deleted_question_id", table_name="questions")
    op.drop_table("questions")
    op.execute("DROP INDEX IF EXISTS uq_users_prn_examinee_active")
    op.execute("DROP INDEX IF EXISTS uq_users_username_examiner")
    op.drop_table("users")

    bind = op.get_bind()
    erasure_job_status.drop(bind, checkfirst=True)
    selected_option.drop(bind, checkfirst=True)
    selection_mode.drop(bind, checkfirst=True)
    session_status.drop(bind, checkfirst=True)
    correct_option.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
