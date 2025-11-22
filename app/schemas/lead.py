from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.lead import LeadStatus, LeadSource


class LeadBase(BaseModel):
    full_name: str
    company_name: Optional[str] = None
    phone: str
    email: EmailStr
    desired_area: Optional[float] = None
    budget: Optional[float] = None
    lease_term: Optional[str] = None
    message: Optional[str] = None


class LeadCreate(LeadBase):
    property_id: Optional[int] = None
    premise_id: Optional[int] = None
    source: LeadSource = LeadSource.WEBSITE
    consent_given: bool = True


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    assigned_to_id: Optional[int] = None
    priority: Optional[int] = None
    viewing_date: Optional[datetime] = None
    viewing_completed: Optional[bool] = None
    rejection_reason: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    property_id: Optional[int]
    premise_id: Optional[int]
    status: LeadStatus
    source: LeadSource
    assigned_to_id: Optional[int]
    priority: int
    viewing_date: Optional[datetime]
    viewing_completed: bool
    created_at: datetime
    contacted_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadCommunicationCreate(BaseModel):
    communication_type: str
    subject: Optional[str] = None
    notes: str
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class LeadCommunicationResponse(LeadCommunicationCreate):
    id: int
    lead_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
