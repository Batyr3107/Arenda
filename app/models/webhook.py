from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class WebhookEvent(str, enum.Enum):
    # Payment events
    PAYMENT_CREATED = "payment.created"
    PAYMENT_APPROVED = "payment.approved"
    PAYMENT_REJECTED = "payment.rejected"
    PAYMENT_OVERDUE = "payment.overdue"

    # Contract events
    CONTRACT_CREATED = "contract.created"
    CONTRACT_ACTIVATED = "contract.activated"
    CONTRACT_TERMINATED = "contract.terminated"
    CONTRACT_EXPIRING = "contract.expiring"

    # Tenant events
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"

    # Lead events
    LEAD_CREATED = "lead.created"
    LEAD_CONVERTED = "lead.converted"


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    events = Column(JSON, nullable=False)  # List of WebhookEvent values
    is_active = Column(Boolean, default=True, index=True)

    # Security
    secret = Column(String, nullable=True)  # For HMAC signature

    # Headers (optional)
    custom_headers = Column(JSON, nullable=True)

    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime(timezone=True), nullable=True)
    last_delivery_status = Column(String, nullable=True)

    # Owner
    created_by_id = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Webhook {self.name} - {self.url}>"


class WebhookDelivery(Base):
    """Log of webhook delivery attempts"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)

    webhook_id = Column(Integer, nullable=False, index=True)
    event_type = Column(SQLEnum(WebhookEvent), nullable=False, index=True)

    # Request
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)

    # Response
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Status
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Retry info
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<WebhookDelivery webhook#{self.webhook_id} {self.event_type} - {'✓' if self.success else '✗'}>"
