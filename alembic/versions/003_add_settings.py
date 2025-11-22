"""add settings

Revision ID: 003
Revises: 002
Create Date: 2025-11-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False, server_default='Property Management System'),
        sa.Column('company_logo_url', sa.String(), nullable=True),
        sa.Column('support_email', sa.String(), nullable=True),
        sa.Column('support_phone', sa.String(), nullable=True),
        sa.Column('default_currency', sa.String(), nullable=False, server_default='KZT'),
        sa.Column('default_late_fee_percentage', sa.String(), nullable=False, server_default='0.5'),
        sa.Column('payment_reminder_days', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('contract_expiry_notice_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('email_notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_from_name', sa.String(), nullable=False, server_default='Property Management'),
        sa.Column('email_from_address', sa.String(), nullable=True),
        sa.Column('sms_notifications_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sms_provider', sa.String(), nullable=True),
        sa.Column('sms_api_key', sa.String(), nullable=True),
        sa.Column('enable_public_catalog', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_lead_management', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_webhooks', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_audit_log', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('require_two_stage_approval', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_generate_payment_schedule', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('custom_settings', JSON, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_system_settings_id', 'system_settings', ['id'])

    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('available_variables', JSON, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_index('ix_email_templates_id', 'email_templates', ['id'])
    op.create_index('ix_email_templates_name', 'email_templates', ['name'])

    # Insert default settings
    op.execute("""
        INSERT INTO system_settings (id, company_name, default_currency, default_late_fee_percentage,
                                     payment_reminder_days, contract_expiry_notice_days,
                                     email_from_name)
        VALUES (1, 'Property Management System', 'KZT', '0.5', 3, 30, 'Property Management')
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_email_templates_name', 'email_templates')
    op.drop_index('ix_email_templates_id', 'email_templates')
    op.drop_index('ix_system_settings_id', 'system_settings')

    # Drop tables
    op.drop_table('email_templates')
    op.drop_table('system_settings')
