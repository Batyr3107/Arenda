from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date


class OccupancyReport(BaseModel):
    """Отчет по заполненности объекта"""
    property_id: int
    property_name: str
    total_premises: int
    occupied_premises: int
    available_premises: int
    reserved_premises: int
    occupancy_rate: float  # Процент заполненности


class FinancialReport(BaseModel):
    """Финансовый отчет"""
    period_start: date
    period_end: date
    total_revenue: float
    expected_revenue: float
    received_payments: float
    pending_payments: float
    overdue_payments: float
    total_debt: float


class PropertyFinancialReport(FinancialReport):
    """Финансовый отчет по объекту"""
    property_id: int
    property_name: str


class TenantPaymentReport(BaseModel):
    """Отчет по платежам арендатора"""
    tenant_id: int
    tenant_name: str
    total_paid: float
    total_pending: float
    total_overdue: float
    payment_discipline_rate: float  # Процент своевременных платежей
    average_delay_days: float


class LeadConversionReport(BaseModel):
    """Отчет по конверсии лидов"""
    total_leads: int
    new_leads: int
    contacted_leads: int
    viewing_scheduled: int
    viewed: int
    contracts_signed: int
    rejected: int
    conversion_rate: float  # Процент конверсии в договоры
    average_processing_days: float


class LeadSourceReport(BaseModel):
    """Отчет по источникам лидов"""
    source: str
    count: int
    conversion_rate: float


class DashboardMetrics(BaseModel):
    """Метрики для дашборда"""
    total_properties: int
    total_premises: int
    total_active_contracts: int
    total_active_tenants: int
    total_leads: int
    new_leads_today: int
    occupancy_rate: float
    monthly_revenue: float
    pending_approvals: int
    overdue_payments: int
    overdue_amount: float


class PropertyMetrics(BaseModel):
    """Метрики по объекту"""
    property_id: int
    property_name: str
    total_premises: int
    occupied_premises: int
    occupancy_rate: float
    monthly_revenue: float
    average_price_per_sqm: float
    total_area: float
    occupied_area: float
