from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.scheduled_report import ScheduledReport, ReportExecution, ReportFrequency
from app.schemas.scheduled_report import (
    ScheduledReportCreate, ScheduledReportUpdate,
    ScheduledReportResponse, ReportExecutionResponse
)
from app.api.deps import get_current_user, get_admin_or_higher
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def calculate_next_run(frequency: ReportFrequency, day_of_week: int = None, day_of_month: int = None, time_of_day: str = "09:00") -> datetime:
    """Calculate next run time based on frequency"""
    now = datetime.utcnow()
    hour, minute = map(int, time_of_day.split(":"))

    if frequency == ReportFrequency.DAILY:
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

    elif frequency == ReportFrequency.WEEKLY:
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run += timedelta(days=days_ahead)

    elif frequency == ReportFrequency.MONTHLY:
        next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            # Move to next month
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)

    elif frequency == ReportFrequency.QUARTERLY:
        next_run = now.replace(day=day_of_month or 1, hour=hour, minute=minute, second=0, microsecond=0)
        # Find next quarter
        current_quarter = (now.month - 1) // 3
        next_quarter_month = (current_quarter + 1) * 3 + 1
        if next_quarter_month > 12:
            next_run = next_run.replace(year=next_run.year + 1, month=1)
        else:
            next_run = next_run.replace(month=next_quarter_month)

    else:
        next_run = now + timedelta(days=1)

    return next_run


@router.post("", response_model=ScheduledReportResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    report_data: ScheduledReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Create a new scheduled report"""

    # Validate day_of_week for weekly reports
    if report_data.frequency == ReportFrequency.WEEKLY and (report_data.day_of_week is None or report_data.day_of_week < 0 or report_data.day_of_week > 6):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="day_of_week must be between 0 (Monday) and 6 (Sunday) for weekly reports"
        )

    # Validate day_of_month for monthly reports
    if report_data.frequency in [ReportFrequency.MONTHLY, ReportFrequency.QUARTERLY]:
        if report_data.day_of_month is None or report_data.day_of_month < 1 or report_data.day_of_month > 31:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="day_of_month must be between 1 and 31 for monthly/quarterly reports"
            )

    # Calculate next run time
    next_run = calculate_next_run(
        report_data.frequency,
        report_data.day_of_week,
        report_data.day_of_month,
        report_data.time_of_day
    )

    report = ScheduledReport(
        **report_data.model_dump(),
        created_by_id=current_user.id,
        company_id=current_user.company_id,
        next_run_at=next_run
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report


@router.get("", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List all scheduled reports"""
    query = select(ScheduledReport).where(ScheduledReport.company_id == current_user.company_id)

    if is_active is not None:
        query = query.where(ScheduledReport.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(ScheduledReport.created_at.desc())

    result = await db.execute(query)
    reports = result.scalars().all()

    return reports


@router.get("/{report_id}", response_model=ScheduledReportResponse)
async def get_scheduled_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get scheduled report by ID"""
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found"
        )

    return report


@router.put("/{report_id}", response_model=ScheduledReportResponse)
async def update_scheduled_report(
    report_id: int,
    report_data: ScheduledReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Update scheduled report"""
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found"
        )

    # Update fields
    update_data = report_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    # Recalculate next run if schedule changed
    if any(key in update_data for key in ['frequency', 'day_of_week', 'day_of_month', 'time_of_day']):
        report.next_run_at = calculate_next_run(
            report.frequency,
            report.day_of_week,
            report.day_of_month,
            report.time_of_day
        )

    await db.commit()
    await db.refresh(report)

    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Delete scheduled report"""
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found"
        )

    await db.delete(report)
    await db.commit()

    return None


@router.post("/{report_id}/execute")
async def execute_scheduled_report_now(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Execute a scheduled report immediately"""
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found"
        )

    # Create execution record
    execution = ReportExecution(
        scheduled_report_id=report.id,
        status="running",
        recipients_count=len(report.recipients)
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Here we would trigger the actual report generation
    # For now, just mark as completed
    execution.status = "success"
    execution.completed_at = datetime.utcnow()
    execution.sent_successfully = True

    # Update last run
    report.last_run_at = datetime.utcnow()

    await db.commit()

    return {
        "message": "Report execution started",
        "execution_id": execution.id,
        "status": execution.status
    }


@router.get("/{report_id}/executions", response_model=List[ReportExecutionResponse])
async def list_report_executions(
    report_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List execution history for a scheduled report"""
    query = (
        select(ReportExecution)
        .where(ReportExecution.scheduled_report_id == report_id)
        .offset(skip)
        .limit(limit)
        .order_by(ReportExecution.started_at.desc())
    )

    result = await db.execute(query)
    executions = result.scalars().all()

    return executions
