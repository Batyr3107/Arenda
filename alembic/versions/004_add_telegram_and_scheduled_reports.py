"""Add Telegram integration and Scheduled Reports

Revision ID: 004
Revises: 003
Create Date: 2024-11-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create telegram_users table
    op.create_table(
        'telegram_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('language_code', sa.String(), server_default='ru', nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_notifications_enabled', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_interaction', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_telegram_users_id', 'telegram_users', ['id'])
    op.create_index('ix_telegram_users_telegram_id', 'telegram_users', ['telegram_id'], unique=True)
    op.create_index('ix_telegram_users_user_id', 'telegram_users', ['user_id'])

    # Create telegram_messages table
    op.create_table(
        'telegram_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_user_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('command', sa.String(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['telegram_user_id'], ['telegram_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_telegram_messages_id', 'telegram_messages', ['id'])
    op.create_index('ix_telegram_messages_telegram_user_id', 'telegram_messages', ['telegram_user_id'])
    op.create_index('ix_telegram_messages_command', 'telegram_messages', ['command'])

    # Create scheduled_reports table
    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', name='reportfrequency'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('time_of_day', sa.String(), server_default='09:00', nullable=True),
        sa.Column('format', sa.Enum('PDF', 'EXCEL', 'CSV', name='reportformat'), server_default='PDF', nullable=True),
        sa.Column('recipients', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_reports_id', 'scheduled_reports', ['id'])

    # Create report_executions table
    op.create_table(
        'report_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scheduled_report_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('recipients_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('sent_successfully', sa.Boolean(), server_default='false', nullable=True),
        sa.ForeignKeyConstraint(['scheduled_report_id'], ['scheduled_reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_executions_id', 'report_executions', ['id'])
    op.create_index('ix_report_executions_scheduled_report_id', 'report_executions', ['scheduled_report_id'])


def downgrade():
    op.drop_index('ix_report_executions_scheduled_report_id', table_name='report_executions')
    op.drop_index('ix_report_executions_id', table_name='report_executions')
    op.drop_table('report_executions')

    op.drop_index('ix_scheduled_reports_id', table_name='scheduled_reports')
    op.drop_table('scheduled_reports')
    op.execute('DROP TYPE reportfrequency')
    op.execute('DROP TYPE reportformat')

    op.drop_index('ix_telegram_messages_command', table_name='telegram_messages')
    op.drop_index('ix_telegram_messages_telegram_user_id', table_name='telegram_messages')
    op.drop_index('ix_telegram_messages_id', table_name='telegram_messages')
    op.drop_table('telegram_messages')

    op.drop_index('ix_telegram_users_user_id', table_name='telegram_users')
    op.drop_index('ix_telegram_users_telegram_id', table_name='telegram_users')
    op.drop_index('ix_telegram_users_id', table_name='telegram_users')
    op.drop_table('telegram_users')
