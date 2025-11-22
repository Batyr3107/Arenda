from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date, timedelta
from typing import List, Dict
from app.models.property import Property, Premise, PremiseStatus
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
    """Get financial report for a period"""
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

    # Received payments (approved)
    received_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.due_date >= period_start,
                Payment.due_date <= period_end,
                Payment.status == PaymentStatus.APPROVED
            )
        )
    )
    received_payments = received_result.scalar() or 0.0

    # Pending payments
    pending_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.due_date >= period_start,
                Payment.due_date <= period_end,
                or_(
                    Payment.status == PaymentStatus.PENDING,
                    Payment.status == PaymentStatus.PENDING_APPROVAL
                )
            )
        )
    )
    pending_payments = pending_result.scalar() or 0.0

    # Overdue payments
    overdue_result = await db.execute(
        select(func.sum(Payment.amount + Payment.late_fee)).where(
            and_(
                Payment.due_date >= period_start,
                Payment.due_date <= period_end,
                Payment.status == PaymentStatus.OVERDUE
            )
        )
    )
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

    # Active contracts
    contracts_result = await db.execute(
        select(func.count(Contract.id)).where(
            Contract.status == ContractStatus.ACTIVE
        )
    )
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

    # Total leads
    leads_result = await db.execute(
        select(func.count(Lead.id))
    )
    total_leads = leads_result.scalar() or 0

    # New leads today
    today = date.today()
    new_leads_result = await db.execute(
        select(func.count(Lead.id)).where(
            func.date(Lead.created_at) == today
        )
    )
    new_leads_today = new_leads_result.scalar() or 0

    # Occupancy rate
    occupied_result = await db.execute(
        select(func.count(Premise.id)).where(
            Premise.status == PremiseStatus.OCCUPIED
        )
    )
    occupied = occupied_result.scalar() or 0
    occupancy_rate = (occupied / total_premises * 100) if total_premises > 0 else 0

    # Monthly revenue (current month)
    month_start = date(today.year, today.month, 1)
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.payment_date >= month_start,
                Payment.status == PaymentStatus.APPROVED
            )
        )
    )
    monthly_revenue = revenue_result.scalar() or 0.0

    # Pending approvals
    pending_result = await db.execute(
        select(func.count(Payment.id)).where(
            Payment.status == PaymentStatus.PENDING_APPROVAL
        )
    )
    pending_approvals = pending_result.scalar() or 0

    # Overdue payments
    overdue_count_result = await db.execute(
        select(func.count(Payment.id)).where(
            Payment.status == PaymentStatus.OVERDUE
        )
    )
    overdue_payments = overdue_count_result.scalar() or 0

    overdue_amount_result = await db.execute(
        select(func.sum(Payment.amount + Payment.late_fee)).where(
            Payment.status == PaymentStatus.OVERDUE
        )
    )
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


async def get_lead_conversion_report(db: AsyncSession) -> LeadConversionReport:
    """Get lead conversion statistics"""
    # Total leads
    total_result = await db.execute(
        select(func.count(Lead.id))
    )
    total_leads = total_result.scalar() or 0

    # Counts by status
    new_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.NEW)
    )
    new_leads = new_result.scalar() or 0

    contacted_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONTACTED)
    )
    contacted_leads = contacted_result.scalar() or 0

    viewing_scheduled_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.VIEWING_SCHEDULED)
    )
    viewing_scheduled = viewing_scheduled_result.scalar() or 0

    viewed_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.VIEWED)
    )
    viewed = viewed_result.scalar() or 0

    contracts_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.CONTRACT_SIGNED)
    )
    contracts_signed = contracts_result.scalar() or 0

    rejected_result = await db.execute(
        select(func.count(Lead.id)).where(
            or_(
                Lead.status == LeadStatus.REJECTED_BY_CLIENT,
                Lead.status == LeadStatus.REJECTED_BY_COMPANY,
                Lead.status == LeadStatus.LOST
            )
        )
    )
    rejected = rejected_result.scalar() or 0

    conversion_rate = (contracts_signed / total_leads * 100) if total_leads > 0 else 0

    # Average processing days (for converted leads)
    avg_days_result = await db.execute(
        select(func.avg(
            func.julianday(Lead.updated_at) - func.julianday(Lead.created_at)
        )).where(Lead.status == LeadStatus.CONTRACT_SIGNED)
    )
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
