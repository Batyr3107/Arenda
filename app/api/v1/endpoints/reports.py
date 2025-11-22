from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from app.db.session import get_db
from app.models.user import User
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models.property import Property, Premise
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
from app.utils.export import (
    export_to_csv, export_to_excel,
    payments_to_export_dict, tenants_to_export_dict,
    contracts_to_export_dict, properties_to_export_dict,
    premises_to_export_dict
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


# Export endpoints
@router.get("/export/payments")
async def export_payments(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    period_start: date = Query(None),
    period_end: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export payments to Excel or CSV"""
    query = select(Payment)

    if period_start:
        query = query.where(Payment.due_date >= period_start)
    if period_end:
        query = query.where(Payment.due_date <= period_end)

    result = await db.execute(query.order_by(Payment.created_at.desc()))
    payments = result.scalars().all()

    # Convert to dict
    data = payments_to_export_dict(payments)

    columns = [
        'ID', 'Номер платежа', 'Договор ID', 'Тип платежа', 'Сумма',
        'Статус', 'Срок оплаты', 'Дата оплаты', 'Дней просрочки',
        'Пеня', 'Создан', 'Описание'
    ]

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"payments_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, "Платежи")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"payments_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/tenants")
async def export_tenants(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export tenants to Excel or CSV"""
    query = select(Tenant)

    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)

    result = await db.execute(query.order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()

    # Convert to dict
    data = tenants_to_export_dict(tenants)

    columns = [
        'ID', 'Название', 'Тип', 'БИН/ИИН', 'Email', 'Телефон',
        'Адрес', 'Активен', 'Создан', 'Обновлен'
    ]

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"tenants_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, "Арендаторы")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"tenants_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/contracts")
async def export_contracts(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export contracts to Excel or CSV"""
    result = await db.execute(select(Contract).order_by(Contract.created_at.desc()))
    contracts = result.scalars().all()

    # Convert to dict
    data = contracts_to_export_dict(contracts)

    columns = [
        'ID', 'Номер договора', 'Арендатор ID', 'Помещение ID',
        'Дата начала', 'Дата окончания', 'Ежемесячная арендная плата',
        'Депозит', 'Статус', 'Частота платежей', 'День платежа',
        'Процент пени', 'Создан', 'Подписан'
    ]

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"contracts_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, "Договоры")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"contracts_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/properties")
async def export_properties(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export properties to Excel or CSV"""
    result = await db.execute(select(Property).order_by(Property.created_at.desc()))
    properties = result.scalars().all()

    # Convert to dict
    data = properties_to_export_dict(properties)

    columns = [
        'ID', 'Название', 'Тип', 'Адрес', 'Город', 'Общая площадь',
        'Компания ID', 'Создан', 'Описание'
    ]

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"properties_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, "Объекты")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"properties_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/premises")
async def export_premises(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export premises to Excel or CSV"""
    result = await db.execute(select(Premise).order_by(Premise.created_at.desc()))
    premises = result.scalars().all()

    # Convert to dict
    data = premises_to_export_dict(premises)

    columns = [
        'ID', 'Номер', 'Здание ID', 'Этаж', 'Площадь', 'Тип',
        'Статус', 'Цена в месяц', 'Опубликован', 'Создан', 'Описание'
    ]

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"premises_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, "Помещения")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"premises_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
