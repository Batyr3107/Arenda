from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.webhook import WebhookEvent


class WebhookBase(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = None
    events: List[WebhookEvent]
    is_active: bool = True
    secret: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
    events: Optional[List[WebhookEvent]] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str]
    events: List[str]
    is_active: bool
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: Optional[datetime]
    last_delivery_status: Optional[str]
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: int
    webhook_id: int
    event_type: WebhookEvent
    payload: Dict[str, Any]
    status_code: Optional[int]
    response_body: Optional[str]
    response_time_ms: Optional[int]
    success: bool
    error_message: Optional[str]
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookTestRequest(BaseModel):
    test_data: Optional[Dict[str, Any]] = None
