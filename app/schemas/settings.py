from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class SystemSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    default_currency: Optional[str] = None
    default_late_fee_percentage: Optional[str] = None
    payment_reminder_days: Optional[int] = None
    contract_expiry_notice_days: Optional[int] = None
    email_notifications_enabled: Optional[bool] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[EmailStr] = None
    sms_notifications_enabled: Optional[bool] = None
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    enable_public_catalog: Optional[bool] = None
    enable_lead_management: Optional[bool] = None
    enable_webhooks: Optional[bool] = None
    enable_audit_log: Optional[bool] = None
    require_two_stage_approval: Optional[bool] = None
    auto_generate_payment_schedule: Optional[bool] = None
    custom_settings: Optional[Dict[str, Any]] = None


class SystemSettingsResponse(BaseModel):
    id: int
    company_name: str
    company_logo_url: Optional[str]
    support_email: Optional[str]
    support_phone: Optional[str]
    default_currency: str
    default_late_fee_percentage: str
    payment_reminder_days: int
    contract_expiry_notice_days: int
    email_notifications_enabled: bool
    email_from_name: str
    email_from_address: Optional[str]
    sms_notifications_enabled: bool
    sms_provider: Optional[str]
    enable_public_catalog: bool
    enable_lead_management: bool
    enable_webhooks: bool
    enable_audit_log: bool
    require_two_stage_approval: bool
    auto_generate_payment_schedule: bool
    custom_settings: Optional[Dict[str, Any]]
    updated_at: Optional[datetime]
    updated_by_id: Optional[int]

    class Config:
        from_attributes = True


class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    description: Optional[str] = None
    available_variables: Optional[List[str]] = None
    is_active: bool = True


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    description: Optional[str] = None
    available_variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body_html: str
    body_text: Optional[str]
    description: Optional[str]
    available_variables: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by_id: Optional[int]

    class Config:
        from_attributes = True
