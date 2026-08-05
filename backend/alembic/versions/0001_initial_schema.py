"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "agent", "user", name="user_role", native_enum=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "waiting_on_user", "resolved", "closed", name="ticket_status", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "urgent", name="ticket_priority", native_enum=False),
            nullable=False,
        ),
        sa.Column("requester_id", sa.String(length=36), nullable=False),
        sa.Column("assigned_to_id", sa.String(length=36), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_requester_id"), "tickets", ["requester_id"], unique=False)
    op.create_index(op.f("ix_tickets_assigned_to_id"), "tickets", ["assigned_to_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_assigned_to_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_requester_id"), table_name="tickets")
    op.drop_table("tickets")
    op.drop_table("users")