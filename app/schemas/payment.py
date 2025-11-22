from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.models.payment import PaymentStatus, PaymentType


class PaymentDocumentBase(BaseModel):
    file_name: str
    description: Optional[str] = None


class PaymentDocumentCreate(PaymentDocumentBase):
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class PaymentDocumentResponse(PaymentDocumentBase):
    id: int
    payment_id: int
    file_url: str
    file_size: Optional[int]
    mime_type: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    contract_id: int
    payment_type: PaymentType = PaymentType.RENT
    amount: float
    due_date: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    payment_number: str


class PaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


class PaymentApprovalRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int
    payment_number: str
    status: PaymentStatus
    payment_date: Optional[date]
    notes: Optional[str]
    late_fee: float
    days_overdue: int
    uploaded_by_id: Optional[int]
    first_approved_by_id: Optional[int]
    second_approved_by_id: Optional[int]
    first_approved_at: Optional[datetime]
    second_approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentDetailResponse(PaymentResponse):
    documents: List[PaymentDocumentResponse] = []

    class Config:
        from_attributes = True


class PaymentUploadRequest(BaseModel):
    """Request for tenant to upload payment proof"""
    payment_id: int
    notes: Optional[str] = None
