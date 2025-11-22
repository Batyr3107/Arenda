from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import (
    OccupancyReport, FinancialReport, DashboardMetrics,
    LeadConversionReport
)
from app.api.deps import get_moderator_or_higher
from app.services.report_service import (
    get_occupancy_report,
    get_financial_report,
    get_dashboard_metrics,
    get_lead_conversion_report
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get dashboard metrics"""
    company_id = current_user.company_id if current_user.role != "super_admin" else None
    metrics = await get_dashboard_metrics(db, company_id)
    return metrics


@router.get("/occupancy/{property_id}", response_model=OccupancyReport)
async def get_property_occupancy(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get occupancy report for a property"""
    report = await get_occupancy_report(db, property_id)
    return report


@router.get("/financial", response_model=FinancialReport)
async def get_financial(
    period_start: date = Query(...),
    period_end: date = Query(...),
    property_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get financial report for a period"""
    report = await get_financial_report(db, period_start, period_end, property_id)
    return report


@router.get("/leads/conversion", response_model=LeadConversionReport)
async def get_lead_conversion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get lead conversion statistics"""
    report = await get_lead_conversion_report(db)
    return report
