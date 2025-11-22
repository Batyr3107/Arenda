from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.models.contract import ContractStatus, PaymentFrequency


class PaymentScheduleBase(BaseModel):
    due_date: date
    amount: float
    description: Optional[str] = None


class PaymentScheduleCreate(PaymentScheduleBase):
    contract_id: int


class PaymentScheduleUpdate(BaseModel):
    due_date: Optional[date] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    is_paid: Optional[bool] = None
    paid_date: Optional[date] = None
    paid_amount: Optional[float] = None


class PaymentScheduleResponse(PaymentScheduleBase):
    id: int
    contract_id: int
    is_paid: bool
    paid_date: Optional[date]
    paid_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class ContractBase(BaseModel):
    tenant_id: int
    premise_id: int
    contract_number: str
    start_date: date
    end_date: date
    monthly_rent: float
    deposit_amount: Optional[float] = None
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    payment_day: int = 1
    late_fee_percentage: float = 0.1
    utilities_included: bool = False
    utilities_cost: Optional[float] = None
    terms_and_conditions: Optional[str] = None
    special_conditions: Optional[str] = None


class ContractCreate(ContractBase):
    signed_date: Optional[date] = None
    status: ContractStatus = ContractStatus.DRAFT


class ContractUpdate(BaseModel):
    status: Optional[ContractStatus] = None
    end_date: Optional[date] = None
    monthly_rent: Optional[float] = None
    deposit_amount: Optional[float] = None
    payment_day: Optional[int] = None
    late_fee_percentage: Optional[float] = None
    utilities_included: Optional[bool] = None
    utilities_cost: Optional[float] = None
    terms_and_conditions: Optional[str] = None
    special_conditions: Optional[str] = None
    contract_file_url: Optional[str] = None


class ContractResponse(ContractBase):
    id: int
    status: ContractStatus
    signed_date: Optional[date]
    contract_file_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ContractDetailResponse(ContractResponse):
    payment_schedules: List[PaymentScheduleResponse] = []

    class Config:
        from_attributes = True
