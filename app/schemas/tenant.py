from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class TenantContactBase(BaseModel):
    full_name: str
    position: Optional[str] = None
    phone: str
    email: Optional[str] = None
    is_primary: bool = False


class TenantContactCreate(TenantContactBase):
    tenant_id: int


class TenantContactUpdate(BaseModel):
    full_name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: Optional[bool] = None


class TenantContactResponse(TenantContactBase):
    id: int
    tenant_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TenantBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    bin_iin: Optional[str] = None
    is_individual: bool = False
    email: str
    phone: str
    address: Optional[str] = None
    website: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bik: Optional[str] = None
    business_type: Optional[str] = None
    notes: Optional[str] = None


class TenantCreate(TenantBase):
    company_id: int


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    bin_iin: Optional[str] = None
    is_individual: Optional[bool] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bik: Optional[str] = None
    business_type: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    contacts: List[TenantContactResponse] = []

    class Config:
        from_attributes = True
