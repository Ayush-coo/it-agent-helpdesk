"""add ticket numbers, comments, events, and number counter

Revision ID: 20261125_0005
Revises: 20261028_0004
"""
from alembic import op
import sqlalchemy as sa


revision = "20261125_0005"
down_revision = "20261028_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("ticket_number", sa.String(length=20), nullable=True))
    connection = op.get_bind()
    tickets = connection.execute(
        sa.text("SELECT id FROM tickets ORDER BY created_at, id")
    ).fetchall()
    for number, (ticket_id,) in enumerate(tickets, start=1):
        connection.execute(
            sa.text("UPDATE tickets SET ticket_number = :ticket_number WHERE id = :ticket_id"),
            {"ticket_number": f"INC-{number:04d}", "ticket_id": ticket_id},
        )

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column("ticket_number", existing_type=sa.String(length=20), nullable=False)
    op.create_index("ix_tickets_ticket_number", "tickets", ["ticket_number"], unique=True)

    op.create_table(
        "ticket_number_counters",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "ticket_number_counters",
            sa.column("id", sa.Integer()),
            sa.column("value", sa.Integer()),
        ),
        [{"id": 1, "value": len(tickets)}],
    )
    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_comments_ticket_id", "ticket_comments", ["ticket_id"])
    op.create_index("ix_ticket_comments_author_id", "ticket_comments", ["author_id"])
    op.create_table(
        "ticket_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])
    op.create_index("ix_ticket_events_actor_id", "ticket_events", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_events_actor_id", table_name="ticket_events")
    op.drop_index("ix_ticket_events_ticket_id", table_name="ticket_events")
    op.drop_table("ticket_events")
    op.drop_index("ix_ticket_comments_author_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_ticket_id", table_name="ticket_comments")
    op.drop_table("ticket_comments")
    op.drop_table("ticket_number_counters")
    op.drop_index("ix_tickets_ticket_number", table_name="tickets")
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_column("ticket_number")
