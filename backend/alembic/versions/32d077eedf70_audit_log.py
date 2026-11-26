"""audit_log

Revision ID: 32d077eedf70
Revises: 0002_enterprise_triage
Create Date: 2026-09-22 05:45:21.390696+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32d077eedf70'
down_revision = '0002_enterprise_triage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('audit_logs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=True),
    sa.Column('user_role', sa.String(length=20), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=True),
    sa.Column('resource_id', sa.String(length=36), nullable=True),
    sa.Column('severity', sa.String(length=4), nullable=True),
    sa.Column('tool_called', sa.String(length=100), nullable=True),
    sa.Column('ai_confidence', sa.Float(), nullable=True),
    sa.Column('telemetry_data', sa.JSON(), nullable=True),
    sa.Column('request_payload', sa.JSON(), nullable=True),
    sa.Column('result_payload', sa.JSON(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    # Skipped ALTER COLUMN statements — SQLite does not support them,
    # and the columns already have the correct schema from migration 0002.


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_table('audit_logs')