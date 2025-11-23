from fastapi import APIRouter, Depends, Query, HTTPException, status
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
from app.utils.repository import get_entity_or_404
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
    # SECURITY: Validate property ownership BEFORE generating report
    property_obj = await get_entity_or_404(db, Property, property_id, "Property")
    if current_user.role != "super_admin" and property_obj.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

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
    # SECURITY: If report has property_id, validate ownership
    if property_id:
        property_obj = await get_entity_or_404(db, Property, property_id, "Property")
        if current_user.role != "super_admin" and property_obj.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    report = await get_financial_report(db, period_start, period_end, property_id)
    return report


@router.get("/leads/conversion", response_model=LeadConversionReport)
async def get_lead_conversion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get lead conversion statistics
    CRITICAL FIX: Added company_id filtering"""
    company_id = current_user.company_id if current_user.role != "super_admin" else None
    report = await get_lead_conversion_report(db, company_id)
    return report


# Export helper function (eliminates duplication)
async def _generic_export(
    model, to_dict_func, columns, sheet_name, filename_prefix,
    format: str, db: AsyncSession, filters=None, joins=None
):
    """Generic export helper - eliminates 150+ lines of duplication
    CRITICAL FIX: Added joins parameter to support company_id filtering via relationships

    Args:
        joins: List of (model, onclause) tuples for JOIN operations
               Example: [(Contract, Payment.contract_id == Contract.id)]
    """
    query = select(model)

    # Apply JOINs (for company_id filtering via relationships)
    if joins:
        for join_model, onclause in joins:
            query = query.join(join_model, onclause, isouter=False)

    # Apply filters (expects list of SQLAlchemy expressions)
    if filters:
        for filter_expression in filters:
            query = query.where(filter_expression)

    result = await db.execute(query.order_by(model.created_at.desc()))
    entities = result.scalars().all()
    data = to_dict_func(entities)

    if format == "csv":
        buffer = export_to_csv(data, columns)
        media_type = "text/csv"
        filename = f"{filename_prefix}_{date.today()}.csv"
    else:
        buffer = export_to_excel(data, columns, sheet_name)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{filename_prefix}_{date.today()}.xlsx"

    return StreamingResponse(buffer, media_type=media_type,
                            headers={"Content-Disposition": f"attachment; filename={filename}"})


# Export endpoints (refactored to use _generic_export)
@router.get("/export/payments")
async def export_payments(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    period_start: date = Query(None),
    period_end: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export payments to Excel or CSV
    CRITICAL FIX: Added company_id filtering via Contract→Tenant relationship"""
    # Build filter list
    filters = []
    if period_start:
        filters.append(Payment.due_date >= period_start)
    if period_end:
        filters.append(Payment.due_date <= period_end)

    # SECURITY: Filter by company_id
    if current_user.role != "super_admin":
        filters.append(Tenant.company_id == current_user.company_id)

    # JOIN Payment→Contract→Tenant to access company_id
    joins = [
        (Contract, Payment.contract_id == Contract.id),
        (Tenant, Contract.tenant_id == Tenant.id)
    ]

    columns = ['ID', 'Номер платежа', 'Договор ID', 'Тип платежа', 'Сумма',
               'Статус', 'Срок оплаты', 'Дата оплаты', 'Дней просрочки',
               'Пеня', 'Создан', 'Описание']

    return await _generic_export(Payment, payments_to_export_dict, columns,
                                 "Платежи", "payments", format, db, filters, joins)


@router.get("/export/tenants")
async def export_tenants(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export tenants to Excel or CSV
    CRITICAL FIX: Added company_id filtering"""
    # Build filter list
    filters = []
    if is_active is not None:
        filters.append(Tenant.is_active == is_active)

    # SECURITY: Filter by company_id (Tenant has company_id directly)
    if current_user.role != "super_admin":
        filters.append(Tenant.company_id == current_user.company_id)

    columns = ['ID', 'Название', 'Тип', 'БИН/ИИН', 'Email', 'Телефон',
               'Адрес', 'Активен', 'Создан', 'Обновлен']

    return await _generic_export(Tenant, tenants_to_export_dict, columns,
                                 "Арендаторы", "tenants", format, db, filters)


@router.get("/export/contracts")
async def export_contracts(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export contracts to Excel or CSV
    CRITICAL FIX: Added company_id filtering via Tenant relationship"""
    # SECURITY: Filter by company_id via Contract→Tenant
    filters = []
    if current_user.role != "super_admin":
        filters.append(Tenant.company_id == current_user.company_id)

    joins = [(Tenant, Contract.tenant_id == Tenant.id)]

    columns = ['ID', 'Номер договора', 'Арендатор ID', 'Помещение ID',
               'Дата начала', 'Дата окончания', 'Ежемесячная арендная плата',
               'Депозит', 'Статус', 'Частота платежей', 'День платежа',
               'Процент пени', 'Создан', 'Подписан']

    return await _generic_export(Contract, contracts_to_export_dict, columns,
                                 "Договоры", "contracts", format, db, filters, joins)


@router.get("/export/properties")
async def export_properties(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export properties to Excel or CSV
    CRITICAL FIX: Added company_id filtering"""
    # SECURITY: Filter by company_id (Property has company_id directly)
    filters = []
    if current_user.role != "super_admin":
        filters.append(Property.company_id == current_user.company_id)

    columns = ['ID', 'Название', 'Тип', 'Адрес', 'Город', 'Общая площадь',
               'Компания ID', 'Создан', 'Описание']

    return await _generic_export(Property, properties_to_export_dict, columns,
                                 "Объекты", "properties", format, db, filters)


@router.get("/export/premises")
async def export_premises(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Export premises to Excel or CSV
    CRITICAL FIX: Added company_id filtering via Building→Property relationship"""
    # SECURITY: Filter by company_id via Premise→Building→Property
    filters = []
    if current_user.role != "super_admin":
        filters.append(Property.company_id == current_user.company_id)

    joins = [
        (Building, Premise.building_id == Building.id),
        (Property, Building.property_id == Property.id)
    ]

    columns = ['ID', 'Номер', 'Здание ID', 'Этаж', 'Площадь', 'Тип',
               'Статус', 'Цена в месяц', 'Опубликован', 'Создан', 'Описание']

    return await _generic_export(Premise, premises_to_export_dict, columns,
                                 "Помещения", "premises", format, db, filters, joins)
