from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    legal_name: str
    bin_iin: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bik: Optional[str] = None
    director_name: Optional[str] = None
    accountant_name: Optional[str] = None
    accountant_phone: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    bin_iin: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bik: Optional[str] = None
    director_name: Optional[str] = None
    accountant_name: Optional[str] = None
    accountant_phone: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
