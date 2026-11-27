"""persist ticket escalation approval requests

Revision ID: 20261127_0007
Revises: 20261125_0006
"""
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20261127_0007"
down_revision = "20261125_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("requester_id", sa.String(length=36), nullable=False),
        sa.Column("approver_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", name="uq_approval_requests_ticket_id"),
    )
    op.create_index("ix_approval_requests_ticket_id", "approval_requests", ["ticket_id"])
    op.create_index("ix_approval_requests_requester_id", "approval_requests", ["requester_id"])
    op.create_index("ix_approval_requests_approver_id", "approval_requests", ["approver_id"])

    connection = op.get_bind()
    pending = connection.execute(
        sa.text(
            "SELECT id, requester_id FROM tickets "
            "WHERE escalation_status = 'pending_review'"
        )
    ).fetchall()
    for ticket_id, requester_id in pending:
        connection.execute(
            sa.text(
                "INSERT INTO approval_requests "
                "(id, ticket_id, requester_id, status) "
                "VALUES (:id, :ticket_id, :requester_id, 'pending')"
            ),
            {"id": str(uuid4()), "ticket_id": ticket_id, "requester_id": requester_id},
        )


def downgrade() -> None:
    op.drop_index("ix_approval_requests_approver_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_requester_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_ticket_id", table_name="approval_requests")
    op.drop_table("approval_requests")
