from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class NotificationType(str, enum.Enum):
    PAYMENT_DUE = "payment_due"
    PAYMENT_OVERDUE = "payment_overdue"
    PAYMENT_RECEIVED = "payment_received"
    CONTRACT_EXPIRING = "contract_expiring"
    CONTRACT_EXPIRED = "contract_expired"
    NEW_LEAD = "new_lead"
    LEAD_UPDATED = "lead_updated"
    VIEWING_SCHEDULED = "viewing_scheduled"
    SYSTEM = "system"


class Notification(Base):
    """Уведомления для пользователей"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String, nullable=True)  # Ссылка на связанный объект

    # Status
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # Отправлено ли по email

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.title}>"
