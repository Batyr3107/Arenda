from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TelegramUserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "ru"


class TelegramUserCreate(TelegramUserBase):
    user_id: Optional[int] = None


class TelegramUserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_notifications_enabled: Optional[bool] = None


class TelegramUserResponse(TelegramUserBase):
    id: int
    user_id: Optional[int]
    is_active: bool
    is_notifications_enabled: bool
    last_interaction: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramLinkRequest(BaseModel):
    """Request to link telegram account with system user"""
    telegram_id: int
    verification_code: str


class TelegramWebhookUpdate(BaseModel):
    """Telegram webhook update"""
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None


class TelegramNotificationRequest(BaseModel):
    """Send notification via telegram"""
    user_id: int
    message: str
    parse_mode: Optional[str] = "HTML"
