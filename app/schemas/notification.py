from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    link: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    is_sent: bool
    created_at: datetime
    read_at: Optional[datetime]
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationMarkRead(BaseModel):
    is_read: bool = True
