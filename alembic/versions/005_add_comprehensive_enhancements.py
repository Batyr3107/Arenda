"""Add comprehensive enhancements: Maintenance, Deposits, Partial Payments, Occupancy History

Revision ID: 005
Revises: 004
Create Date: 2024-11-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to contracts table
    op.add_column('contracts', sa.Column('deposit_paid', sa.Boolean(), server_default='false'))
    op.add_column('contracts', sa.Column('deposit_paid_date', sa.Date(), nullable=True))
    op.add_column('contracts', sa.Column('deposit_refunded', sa.Boolean(), server_default='false'))
    op.add_column('contracts', sa.Column('deposit_refund_amount', sa.Float(), nullable=True))
    op.add_column('contracts', sa.Column('deposit_refund_date', sa.Date(), nullable=True))
    op.add_column('contracts', sa.Column('currency', sa.String(), server_default='KZT'))
    op.add_column('contracts', sa.Column('auto_renew', sa.Boolean(), server_default='false'))
    op.add_column('contracts', sa.Column('renewal_notice_days', sa.Integer(), server_default='30'))
    op.add_column('contracts', sa.Column('early_termination_fee', sa.Float(), nullable=True))
    op.add_column('contracts', sa.Column('is_deleted', sa.Boolean(), server_default='false'))
    op.add_column('contracts', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # Add new fields to payments table
    op.add_column('payments', sa.Column('currency', sa.String(), server_default='KZT'))
    op.add_column('payments', sa.Column('allow_partial_payments', sa.Boolean(), server_default='true'))
    op.add_column('payments', sa.Column('amount_paid', sa.Float(), server_default='0.0'))
    op.add_column('payments', sa.Column('amount_remaining', sa.Float(), nullable=True))
    op.add_column('payments', sa.Column('payment_intent_id', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('payment_provider', sa.String(), nullable=True))

    # Create maintenance_requests table
    op.create_table(
        'maintenance_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('PLUMBING', 'ELECTRICAL', 'HVAC', 'STRUCTURAL', 'APPLIANCES', 'PEST_CONTROL', 'CLEANING', 'SECURITY', 'OTHER', name='maintenancecategory'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='maintenancepriority'), server_default='MEDIUM'),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'ON_HOLD', 'RESOLVED', 'CLOSED', 'CANCELLED', name='maintenancestatus'), server_default='OPEN'),
        sa.Column('premise_id', sa.Integer(), nullable=False),
        sa.Column('building_id', sa.Integer(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('reported_by_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_cost', sa.Integer(), nullable=True),
        sa.Column('actual_cost', sa.Integer(), nullable=True),
        sa.Column('requires_access', sa.Boolean(), server_default='true'),
        sa.Column('access_instructions', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['premise_id'], ['premises.id'], ),
        sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['reported_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_maintenance_requests_id', 'maintenance_requests', ['id'])
    op.create_index('ix_maintenance_requests_status', 'maintenance_requests', ['status'])
    op.create_index('ix_maintenance_requests_premise_id', 'maintenance_requests', ['premise_id'])
    op.create_index('ix_maintenance_requests_reported_by_id', 'maintenance_requests', ['reported_by_id'])

    # Create maintenance_comments table
    op.create_table(
        'maintenance_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('maintenance_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_maintenance_comments_id', 'maintenance_comments', ['id'])
    op.create_index('ix_maintenance_comments_maintenance_request_id', 'maintenance_comments', ['maintenance_request_id'])

    # Create deposit_deductions table
    op.create_table(
        'deposit_deductions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.Enum('DAMAGES', 'CLEANING', 'UNPAID_RENT', 'LATE_FEES', 'UTILITIES', 'OTHER', name='deductionreason'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_file_url', sa.String(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_deposit_deductions_id', 'deposit_deductions', ['id'])
    op.create_index('ix_deposit_deductions_contract_id', 'deposit_deductions', ['contract_id'])

    # Create partial_payments table
    op.create_table(
        'partial_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('transaction_reference', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('processed_by_id', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.ForeignKeyConstraint(['processed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_partial_payments_id', 'partial_payments', ['id'])
    op.create_index('ix_partial_payments_payment_id', 'partial_payments', ['payment_id'])

    # Create occupancy_history table
    op.create_table(
        'occupancy_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('premise_id', sa.Integer(), nullable=False),
        sa.Column('building_id', sa.Integer(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('VACANT', 'OCCUPIED', 'UNDER_RENOVATION', 'RESERVED', name='premisestatus'), nullable=False),
        sa.Column('previous_status', sa.Enum('VACANT', 'OCCUPIED', 'UNDER_RENOVATION', 'RESERVED', name='premisestatus'), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('contract_id', sa.Integer(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['premise_id'], ['premises.id'], ),
        sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_occupancy_history_id', 'occupancy_history', ['id'])
    op.create_index('ix_occupancy_history_premise_id', 'occupancy_history', ['premise_id'])
    op.create_index('ix_occupancy_history_effective_date', 'occupancy_history', ['effective_date'])


def downgrade():
    # Drop occupancy_history table
    op.drop_index('ix_occupancy_history_effective_date', table_name='occupancy_history')
    op.drop_index('ix_occupancy_history_premise_id', table_name='occupancy_history')
    op.drop_index('ix_occupancy_history_id', table_name='occupancy_history')
    op.drop_table('occupancy_history')

    # Drop partial_payments table
    op.drop_index('ix_partial_payments_payment_id', table_name='partial_payments')
    op.drop_index('ix_partial_payments_id', table_name='partial_payments')
    op.drop_table('partial_payments')

    # Drop deposit_deductions table
    op.drop_index('ix_deposit_deductions_contract_id', table_name='deposit_deductions')
    op.drop_index('ix_deposit_deductions_id', table_name='deposit_deductions')
    op.drop_table('deposit_deductions')
    op.execute('DROP TYPE deductionreason')

    # Drop maintenance_comments table
    op.drop_index('ix_maintenance_comments_maintenance_request_id', table_name='maintenance_comments')
    op.drop_index('ix_maintenance_comments_id', table_name='maintenance_comments')
    op.drop_table('maintenance_comments')

    # Drop maintenance_requests table
    op.drop_index('ix_maintenance_requests_reported_by_id', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_premise_id', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_status', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_id', table_name='maintenance_requests')
    op.drop_table('maintenance_requests')
    op.execute('DROP TYPE maintenancestatus')
    op.execute('DROP TYPE maintenancepriority')
    op.execute('DROP TYPE maintenancecategory')

    # Remove columns from payments table
    op.drop_column('payments', 'payment_provider')
    op.drop_column('payments', 'payment_intent_id')
    op.drop_column('payments', 'amount_remaining')
    op.drop_column('payments', 'amount_paid')
    op.drop_column('payments', 'allow_partial_payments')
    op.drop_column('payments', 'currency')

    # Remove columns from contracts table
    op.drop_column('contracts', 'deleted_at')
    op.drop_column('contracts', 'is_deleted')
    op.drop_column('contracts', 'early_termination_fee')
    op.drop_column('contracts', 'renewal_notice_days')
    op.drop_column('contracts', 'auto_renew')
    op.drop_column('contracts', 'currency')
    op.drop_column('contracts', 'deposit_refund_date')
    op.drop_column('contracts', 'deposit_refund_amount')
    op.drop_column('contracts', 'deposit_refunded')
    op.drop_column('contracts', 'deposit_paid_date')
    op.drop_column('contracts', 'deposit_paid')
