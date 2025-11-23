from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date, timedelta
from typing import List, Dict
from app.models.property import Property, Building, Premise, PremiseStatus
from app.models.contract import Contract, ContractStatus
from app.models.payment import Payment, PaymentStatus
from app.models.tenant import Tenant
from app.models.lead import Lead, LeadStatus
from app.schemas.reports import (
    OccupancyReport, FinancialReport, PropertyFinancialReport,
    TenantPaymentReport, LeadConversionReport, DashboardMetrics,
    PropertyMetrics
)


async def get_occupancy_report(db: AsyncSession, property_id: int) -> OccupancyReport:
    """Get occupancy report for a property"""
    # Get property
    property_result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = property_result.scalar_one()

    # Count premises by status
    total_result = await db.execute(
        select(func.count(Premise.id)).join(Building).where(
            Building.property_id == property_id
        )
    )
    total_premises = total_result.scalar() or 0

    occupied_result = await db.execute(
        select(func.count(Premise.id)).join(Building).where(
            and_(
                Building.property_id == property_id,
                Premise.status == PremiseStatus.OCCUPIED
            )
        )
    )
    occupied_premises = occupied_result.scalar() or 0

    available_result = await db.execute(
        select(func.count(Premise.id)).join(Building).where(
            and_(
                Building.property_id == property_id,
                Premise.status == PremiseStatus.AVAILABLE
            )
        )
    )
    available_premises = available_result.scalar() or 0

    reserved_result = await db.execute(
        select(func.count(Premise.id)).join(Building).where(
            and_(
                Building.property_id == property_id,
                Premise.status == PremiseStatus.RESERVED
            )
        )
    )
    reserved_premises = reserved_result.scalar() or 0

    occupancy_rate = (occupied_premises / total_premises * 100) if total_premises > 0 else 0

    return OccupancyReport(
        property_id=property_id,
        property_name=property_obj.name,
        total_premises=total_premises,
        occupied_premises=occupied_premises,
        available_premises=available_premises,
        reserved_premises=reserved_premises,
        occupancy_rate=round(occupancy_rate, 2)
    )


async def get_financial_report(
    db: AsyncSession,
    period_start: date,
    period_end: date,
    property_id: int = None
) -> FinancialReport:
    """Get financial report for a period
    CRITICAL FIX: All payment queries now filter by property_id when specified"""
    # Base query for payments in period
    payment_query = select(Payment).where(
        and_(
            Payment.due_date >= period_start,
            Payment.due_date <= period_end
        )
    )

    # Filter by property if specified
    if property_id:
        payment_query = payment_query.join(Contract).join(Premise).join(Building).where(
            Building.property_id == property_id
        )

    # Total expected revenue
    expected_result = await db.execute(
        select(func.sum(Payment.amount)).select_from(payment_query.subquery())
    )
    expected_revenue = expected_result.scalar() or 0.0

    # Received payments (approved) - CRITICAL FIX: Added property_id filtering
    received_query = select(func.sum(Payment.amount)).where(
        and_(
            Payment.due_date >= period_start,
            Payment.due_date <= period_end,
            Payment.status == PaymentStatus.APPROVED
        )
    )
    if property_id:
        received_query = received_query.join(Contract).join(Premise).join(Building).where(
            Building.property_id == property_id
        )
    received_result = await db.execute(received_query)
    received_payments = received_result.scalar() or 0.0

    # Pending payments - CRITICAL FIX: Added property_id filtering
    pending_query = select(func.sum(Payment.amount)).where(
        and_(
            Payment.due_date >= period_start,
            Payment.due_date <= period_end,
            or_(
                Payment.status == PaymentStatus.PENDING,
                Payment.status == PaymentStatus.PENDING_APPROVAL
            )
        )
    )
    if property_id:
        pending_query = pending_query.join(Contract).join(Premise).join(Building).where(
            Building.property_id == property_id
        )
    pending_result = await db.execute(pending_query)
    pending_payments = pending_result.scalar() or 0.0

    # Overdue payments - CRITICAL FIX: Added property_id filtering
    overdue_query = select(func.sum(Payment.amount + Payment.late_fee)).where(
        and_(
            Payment.due_date >= period_start,
            Payment.due_date <= period_end,
            Payment.status == PaymentStatus.OVERDUE
        )
    )
    if property_id:
        overdue_query = overdue_query.join(Contract).join(Premise).join(Building).where(
            Building.property_id == property_id
        )
    overdue_result = await db.execute(overdue_query)
    overdue_payments = overdue_result.scalar() or 0.0

    total_debt = pending_payments + overdue_payments

    return FinancialReport(
        period_start=period_start,
        period_end=period_end,
        total_revenue=received_payments,
        expected_revenue=expected_revenue,
        received_payments=received_payments,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        total_debt=total_debt
    )


async def get_dashboard_metrics(db: AsyncSession, company_id: int = None) -> DashboardMetrics:
    """Get metrics for main dashboard"""
    # Total properties
    properties_result = await db.execute(
        select(func.count(Property.id)).where(
            Property.company_id == company_id if company_id else True
        )
    )
    total_properties = properties_result.scalar() or 0

    # Total premises
    premises_query = select(func.count(Premise.id))
    if company_id:
        premises_query = premises_query.join(Building).join(Property).where(
            Property.company_id == company_id
        )
    premises_result = await db.execute(premises_query)
    total_premises = premises_result.scalar() or 0

    # Active contracts - CRITICAL FIX: Added company_id filtering
    contracts_query = select(func.count(Contract.id)).where(
        Contract.status == ContractStatus.ACTIVE
    )
    if company_id:
        contracts_query = contracts_query.join(Tenant).where(Tenant.company_id == company_id)
    contracts_result = await db.execute(contracts_query)
    total_active_contracts = contracts_result.scalar() or 0

    # Active tenants
    tenants_result = await db.execute(
        select(func.count(Tenant.id)).where(
            and_(
                Tenant.is_active == True,
                Tenant.company_id == company_id if company_id else True
            )
        )
    )
    total_active_tenants = tenants_result.scalar() or 0

    # Total leads - CRITICAL FIX: Added company_id filtering
    leads_query = select(func.count(Lead.id))
    if company_id:
        leads_query = leads_query.where(Lead.company_id == company_id)
    leads_result = await db.execute(leads_query)
    total_leads = leads_result.scalar() or 0

    # New leads today - CRITICAL FIX: Added company_id filtering
    today = date.today()
    new_leads_query = select(func.count(Lead.id)).where(
        func.date(Lead.created_at) == today
    )
    if company_id:
        new_leads_query = new_leads_query.where(Lead.company_id == company_id)
    new_leads_result = await db.execute(new_leads_query)
    new_leads_today = new_leads_result.scalar() or 0

    # Occupancy rate - CRITICAL FIX: Added company_id filtering
    occupied_query = select(func.count(Premise.id)).where(
        Premise.status == PremiseStatus.OCCUPIED
    )
    if company_id:
        occupied_query = occupied_query.join(Building).join(Property).where(
            Property.company_id == company_id
        )
    occupied_result = await db.execute(occupied_query)
    occupied = occupied_result.scalar() or 0
    occupancy_rate = (occupied / total_premises * 100) if total_premises > 0 else 0

    # Monthly revenue (current month) - CRITICAL FIX: Added company_id filtering
    month_start = date(today.year, today.month, 1)
    revenue_query = select(func.sum(Payment.amount)).where(
        and_(
            Payment.payment_date >= month_start,
            Payment.status == PaymentStatus.APPROVED
        )
    )
    if company_id:
        revenue_query = revenue_query.join(Contract).join(Tenant).where(
            Tenant.company_id == company_id
        )
    revenue_result = await db.execute(revenue_query)
    monthly_revenue = revenue_result.scalar() or 0.0

    # Pending approvals - CRITICAL FIX: Added company_id filtering
    pending_query = select(func.count(Payment.id)).where(
        Payment.status == PaymentStatus.PENDING_APPROVAL
    )
    if company_id:
        pending_query = pending_query.join(Contract).join(Tenant).where(
            Tenant.company_id == company_id
        )
    pending_result = await db.execute(pending_query)
    pending_approvals = pending_result.scalar() or 0

    # Overdue payments - CRITICAL FIX: Added company_id filtering
    overdue_count_query = select(func.count(Payment.id)).where(
        Payment.status == PaymentStatus.OVERDUE
    )
    if company_id:
        overdue_count_query = overdue_count_query.join(Contract).join(Tenant).where(
            Tenant.company_id == company_id
        )
    overdue_count_result = await db.execute(overdue_count_query)
    overdue_payments = overdue_count_result.scalar() or 0

    overdue_amount_query = select(func.sum(Payment.amount + Payment.late_fee)).where(
        Payment.status == PaymentStatus.OVERDUE
    )
    if company_id:
        overdue_amount_query = overdue_amount_query.join(Contract).join(Tenant).where(
            Tenant.company_id == company_id
        )
    overdue_amount_result = await db.execute(overdue_amount_query)
    overdue_amount = overdue_amount_result.scalar() or 0.0

    return DashboardMetrics(
        total_properties=total_properties,
        total_premises=total_premises,
        total_active_contracts=total_active_contracts,
        total_active_tenants=total_active_tenants,
        total_leads=total_leads,
        new_leads_today=new_leads_today,
        occupancy_rate=round(occupancy_rate, 2),
        monthly_revenue=monthly_revenue,
        pending_approvals=pending_approvals,
        overdue_payments=overdue_payments,
        overdue_amount=overdue_amount
    )


async def get_lead_conversion_report(db: AsyncSession, company_id: int = None) -> LeadConversionReport:
    """Get lead conversion statistics
    CRITICAL FIX: Added company_id parameter and filtering to all queries"""
    # Total leads - CRITICAL FIX: Added company_id filtering
    total_query = select(func.count(Lead.id))
    if company_id:
        total_query = total_query.where(Lead.company_id == company_id)
    total_result = await db.execute(total_query)
    total_leads = total_result.scalar() or 0

    # Counts by status - CRITICAL FIX: Added company_id filtering
    new_query = select(func.count(Lead.id)).where(Lead.status == LeadStatus.NEW)
    if company_id:
        new_query = new_query.where(Lead.company_id == company_id)
    new_result = await db.execute(new_query)
    new_leads = new_result.scalar() or 0

    contacted_query = select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONTACTED)
    if company_id:
        contacted_query = contacted_query.where(Lead.company_id == company_id)
    contacted_result = await db.execute(contacted_query)
    contacted_leads = contacted_result.scalar() or 0

    viewing_scheduled_query = select(func.count(Lead.id)).where(Lead.status == LeadStatus.VIEWING_SCHEDULED)
    if company_id:
        viewing_scheduled_query = viewing_scheduled_query.where(Lead.company_id == company_id)
    viewing_scheduled_result = await db.execute(viewing_scheduled_query)
    viewing_scheduled = viewing_scheduled_result.scalar() or 0

    viewed_query = select(func.count(Lead.id)).where(Lead.status == LeadStatus.VIEWED)
    if company_id:
        viewed_query = viewed_query.where(Lead.company_id == company_id)
    viewed_result = await db.execute(viewed_query)
    viewed = viewed_result.scalar() or 0

    contracts_query = select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONTRACT_SIGNED)
    if company_id:
        contracts_query = contracts_query.where(Lead.company_id == company_id)
    contracts_result = await db.execute(contracts_query)
    contracts_signed = contracts_result.scalar() or 0

    rejected_query = select(func.count(Lead.id)).where(
        or_(
            Lead.status == LeadStatus.REJECTED_BY_CLIENT,
            Lead.status == LeadStatus.REJECTED_BY_COMPANY,
            Lead.status == LeadStatus.LOST
        )
    )
    if company_id:
        rejected_query = rejected_query.where(Lead.company_id == company_id)
    rejected_result = await db.execute(rejected_query)
    rejected = rejected_result.scalar() or 0

    conversion_rate = (contracts_signed / total_leads * 100) if total_leads > 0 else 0

    # Average processing days (for converted leads) - CRITICAL FIX: Added company_id filtering
    avg_days_query = select(func.avg(
        func.julianday(Lead.updated_at) - func.julianday(Lead.created_at)
    )).where(Lead.status == LeadStatus.CONTRACT_SIGNED)
    if company_id:
        avg_days_query = avg_days_query.where(Lead.company_id == company_id)
    avg_days_result = await db.execute(avg_days_query)
    average_processing_days = avg_days_result.scalar() or 0.0

    return LeadConversionReport(
        total_leads=total_leads,
        new_leads=new_leads,
        contacted_leads=contacted_leads,
        viewing_scheduled=viewing_scheduled,
        viewed=viewed,
        contracts_signed=contracts_signed,
        rejected=rejected,
        conversion_rate=round(conversion_rate, 2),
        average_processing_days=round(average_processing_days, 1)
    )
