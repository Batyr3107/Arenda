"""add webhooks

Revision ID: 002
Revises: 001
Create Date: 2025-11-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('events', JSON, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('secret', sa.String(), nullable=True),
        sa.Column('custom_headers', JSON, nullable=True),
        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_delivery_status', sa.String(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_webhooks_id', 'webhooks', ['id'])
    op.create_index('ix_webhooks_is_active', 'webhooks', ['is_active'])

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum(
            'PAYMENT_CREATED', 'PAYMENT_APPROVED', 'PAYMENT_REJECTED', 'PAYMENT_OVERDUE',
            'CONTRACT_CREATED', 'CONTRACT_ACTIVATED', 'CONTRACT_TERMINATED', 'CONTRACT_EXPIRING',
            'TENANT_CREATED', 'TENANT_UPDATED',
            'LEAD_CREATED', 'LEAD_CONVERTED',
            name='webhookevent'
        ), nullable=False),
        sa.Column('payload', JSON, nullable=False),
        sa.Column('headers', JSON, nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_webhook_deliveries_id', 'webhook_deliveries', ['id'])
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_index('ix_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'])
    op.create_index('ix_webhook_deliveries_success', 'webhook_deliveries', ['success'])
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_webhook_deliveries_created_at', 'webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_success', 'webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_event_type', 'webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_id', 'webhook_deliveries')

    op.drop_index('ix_webhooks_is_active', 'webhooks')
    op.drop_index('ix_webhooks_id', 'webhooks')

    # Drop tables
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')

    # Drop enum types
    op.execute('DROP TYPE webhookevent')
