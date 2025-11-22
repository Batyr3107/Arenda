from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Dict
from app.db.session import get_db
from app.models.user import User
from app.models.payment import Payment, PaymentStatus
from app.models.contract import Contract, ContractStatus
from app.models.tenant import Tenant
from app.models.property import Premise, PremiseStatus
from app.models.lead import Lead, LeadStatus
from app.api.deps import get_moderator_or_higher
from pydantic import BaseModel

router = APIRouter()


class RevenueByMonth(BaseModel):
    month: str  # Format: "2024-01"
    revenue: float
    payments_count: int


class OccupancyTrend(BaseModel):
    date: str
    total_premises: int
    occupied: int
    available: int
    occupancy_rate: float


class TenantRetention(BaseModel):
    total_tenants: int
    active_tenants: int
    inactive_tenants: int
    retention_rate: float
    avg_contract_length_days: float


class PaymentDiscipline(BaseModel):
    total_payments: int
    on_time: int
    late: int
    overdue: int
    on_time_rate: float
    avg_days_late: float


class LeadSourceStats(BaseModel):
    source: str
    count: int
    converted: int
    conversion_rate: float


@router.get("/revenue-by-month", response_model=List[RevenueByMonth])
async def get_revenue_by_month(
    months: int = Query(12, ge=1, le=24, description="Number of months to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Get revenue statistics grouped by month
    Shows payment trends over time
    """
    # Calculate start date
    today = date.today()
    start_date = today - timedelta(days=months * 30)

    # Query payments grouped by month
    result = await db.execute(
        select(
            func.to_char(Payment.payment_date, 'YYYY-MM').label('month'),
            func.sum(Payment.amount).label('revenue'),
            func.count(Payment.id).label('payments_count')
        )
        .where(
            Payment.payment_date >= start_date,
            Payment.status == PaymentStatus.APPROVED
        )
        .group_by('month')
        .order_by('month')
    )

    data = []
    for row in result:
        data.append(RevenueByMonth(
            month=row.month,
            revenue=float(row.revenue or 0),
            payments_count=row.payments_count or 0
        ))

    return data


@router.get("/occupancy-trend", response_model=List[OccupancyTrend])
async def get_occupancy_trend(
    days: int = Query(30, ge=7, le=90, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Get occupancy trend over time
    Note: This is current snapshot - historical tracking would require additional table
    """
    # Get current stats
    total_result = await db.execute(
        select(func.count(Premise.id))
    )
    total_premises = total_result.scalar() or 0

    occupied_result = await db.execute(
        select(func.count(Premise.id))
        .where(Premise.status == PremiseStatus.OCCUPIED)
    )
    occupied = occupied_result.scalar() or 0

    available = total_premises - occupied
    occupancy_rate = (occupied / total_premises * 100) if total_premises > 0 else 0

    # For now, return current snapshot
    # TODO: Implement historical occupancy tracking
    data = []
    current_date = date.today()

    for i in range(days):
        day = current_date - timedelta(days=i)
        data.append(OccupancyTrend(
            date=day.isoformat(),
            total_premises=total_premises,
            occupied=occupied,
            available=available,
            occupancy_rate=round(occupancy_rate, 2)
        ))

    return list(reversed(data))


@router.get("/tenant-retention", response_model=TenantRetention)
async def get_tenant_retention(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Get tenant retention statistics
    Shows how well the business retains tenants
    """
    # Total tenants
    total_result = await db.execute(
        select(func.count(Tenant.id))
    )
    total_tenants = total_result.scalar() or 0

    # Active tenants
    active_result = await db.execute(
        select(func.count(Tenant.id))
        .where(Tenant.is_active == True)
    )
    active_tenants = active_result.scalar() or 0

    inactive_tenants = total_tenants - active_tenants
    retention_rate = (active_tenants / total_tenants * 100) if total_tenants > 0 else 0

    # Average contract length
    avg_result = await db.execute(
        select(
            func.avg(
                extract('epoch', Contract.end_date) - extract('epoch', Contract.start_date)
            ) / 86400  # Convert seconds to days
        )
        .where(Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.COMPLETED]))
    )
    avg_contract_length = avg_result.scalar() or 0

    return TenantRetention(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        inactive_tenants=inactive_tenants,
        retention_rate=round(retention_rate, 2),
        avg_contract_length_days=round(float(avg_contract_length), 1)
    )


@router.get("/payment-discipline", response_model=PaymentDiscipline)
async def get_payment_discipline(
    months: int = Query(6, ge=1, le=12, description="Number of months to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Get payment discipline statistics
    Shows how well tenants pay on time
    """
    start_date = date.today() - timedelta(days=months * 30)

    # Total payments
    total_result = await db.execute(
        select(func.count(Payment.id))
        .where(Payment.due_date >= start_date)
    )
    total_payments = total_result.scalar() or 0

    # On-time payments (paid before or on due date)
    on_time_result = await db.execute(
        select(func.count(Payment.id))
        .where(
            Payment.due_date >= start_date,
            Payment.status == PaymentStatus.APPROVED,
            Payment.payment_date <= Payment.due_date
        )
    )
    on_time = on_time_result.scalar() or 0

    # Late payments (paid after due date)
    late_result = await db.execute(
        select(func.count(Payment.id))
        .where(
            Payment.due_date >= start_date,
            Payment.status == PaymentStatus.APPROVED,
            Payment.payment_date > Payment.due_date
        )
    )
    late = late_result.scalar() or 0

    # Overdue payments
    overdue_result = await db.execute(
        select(func.count(Payment.id))
        .where(
            Payment.due_date >= start_date,
            Payment.status == PaymentStatus.OVERDUE
        )
    )
    overdue = overdue_result.scalar() or 0

    on_time_rate = (on_time / total_payments * 100) if total_payments > 0 else 0

    # Average days late
    avg_days_result = await db.execute(
        select(func.avg(Payment.days_overdue))
        .where(
            Payment.due_date >= start_date,
            Payment.days_overdue > 0
        )
    )
    avg_days_late = avg_days_result.scalar() or 0

    return PaymentDiscipline(
        total_payments=total_payments,
        on_time=on_time,
        late=late,
        overdue=overdue,
        on_time_rate=round(on_time_rate, 2),
        avg_days_late=round(float(avg_days_late), 1)
    )


@router.get("/lead-sources", response_model=List[LeadSourceStats])
async def get_lead_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Get statistics by lead source
    Shows which marketing channels are most effective
    """
    # Get all leads grouped by source
    result = await db.execute(
        select(
            Lead.source,
            func.count(Lead.id).label('count'),
            func.sum(
                func.case(
                    (Lead.status == LeadStatus.CONVERTED, 1),
                    else_=0
                )
            ).label('converted')
        )
        .group_by(Lead.source)
        .order_by(func.count(Lead.id).desc())
    )

    data = []
    for row in result:
        count = row.count or 0
        converted = row.converted or 0
        conversion_rate = (converted / count * 100) if count > 0 else 0

        data.append(LeadSourceStats(
            source=row.source or "Unknown",
            count=count,
            converted=converted,
            conversion_rate=round(conversion_rate, 2)
        ))

    return data
