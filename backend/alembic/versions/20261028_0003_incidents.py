"""add probable incident detection tables

Revision ID: 20261028_0003
Revises: 32d077eedf70
"""
from alembic import op
import sqlalchemy as sa


revision = "20261028_0003"
down_revision = "32d077eedf70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.Enum("probable", "confirmed", "resolved", name="incident_status", native_enum=False), nullable=False),
        sa.Column("service", sa.String(length=120), nullable=True),
        sa.Column("site", sa.String(length=120), nullable=True),
        sa.Column("subnet", sa.String(length=120), nullable=True),
        sa.Column("asset_group", sa.String(length=120), nullable=True),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("root_cause_hypothesis", sa.Text(), nullable=True),
        sa.Column("suggested_owner", sa.String(length=120), nullable=True),
        sa.Column("timeline", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "incident_tickets",
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("incident_id", "ticket_id"),
    )
    for column in (
        sa.Column("service", sa.String(length=120), nullable=True),
        sa.Column("site", sa.String(length=120), nullable=True),
        sa.Column("subnet", sa.String(length=120), nullable=True),
        sa.Column("asset_group", sa.String(length=120), nullable=True),
        sa.Column("incident_id", sa.String(length=36), nullable=True),
        sa.Column("incident_escalation_suppressed", sa.Boolean(), nullable=False, server_default=sa.false()),
    ):
        op.add_column("tickets", column)
    op.create_index("ix_tickets_service", "tickets", ["service"])
    op.create_index("ix_tickets_site", "tickets", ["site"])
    op.create_index("ix_tickets_incident_id", "tickets", ["incident_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_incident_id", table_name="tickets")
    op.drop_index("ix_tickets_site", table_name="tickets")
    op.drop_index("ix_tickets_service", table_name="tickets")
    op.drop_column("tickets", "incident_escalation_suppressed")
    op.drop_column("tickets", "incident_id")
    op.drop_column("tickets", "asset_group")
    op.drop_column("tickets", "subnet")
    op.drop_column("tickets", "site")
    op.drop_column("tickets", "service")
    op.drop_table("incident_tickets")
    op.drop_table("incidents")
