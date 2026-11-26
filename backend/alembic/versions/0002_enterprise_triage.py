"""add antigravity enterprise columns to tickets

Revision ID: 0002_enterprise_triage
Revises: 0001_initial_schema
Create Date: 2026-09-15 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_enterprise_triage"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- severity (ITIL P1-P4) ---
    op.add_column(
        "tickets",
        sa.Column(
            "severity",
            sa.Enum("P1", "P2", "P3", "P4", name="severity_level", native_enum=False),
            nullable=False,
            server_default="P4",
        ),
    )

    # --- escalation_status ---
    op.add_column(
        "tickets",
        sa.Column(
            "escalation_status",
            sa.Enum(
                "none", "pending_review", "approved", "rejected", "auto_resolved",
                name="escalation_status",
                native_enum=False,
            ),
            nullable=False,
            server_default="none",
        ),
    )

    # --- diagnostic_trail (JSON) ---
    op.add_column(
        "tickets",
        sa.Column("diagnostic_trail", sa.JSON(), nullable=True),
    )

    # --- affected_assets (JSON) ---
    op.add_column(
        "tickets",
        sa.Column("affected_assets", sa.JSON(), nullable=True),
    )

    # --- recommended_agent ---
    op.add_column(
        "tickets",
        sa.Column("recommended_agent", sa.String(length=100), nullable=True),
    )

    # --- runbook_result (JSON) ---
    op.add_column(
        "tickets",
        sa.Column("runbook_result", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tickets", "runbook_result")
    op.drop_column("tickets", "recommended_agent")
    op.drop_column("tickets", "affected_assets")
    op.drop_column("tickets", "diagnostic_trail")
    op.drop_column("tickets", "escalation_status")
    op.drop_column("tickets", "severity")
