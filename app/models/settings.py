from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class SystemSettings(Base):
    """System-wide settings"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)

    # General settings
    company_name = Column(String, default="Property Management System")
    company_logo_url = Column(String, nullable=True)
    support_email = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)

    # Business settings
    default_currency = Column(String, default="KZT")
    default_late_fee_percentage = Column(String, default="0.5")  # % per day
    payment_reminder_days = Column(Integer, default=3)  # Days before due date
    contract_expiry_notice_days = Column(Integer, default=30)

    # Email settings
    email_notifications_enabled = Column(Boolean, default=True)
    email_from_name = Column(String, default="Property Management")
    email_from_address = Column(String, nullable=True)

    # SMS settings
    sms_notifications_enabled = Column(Boolean, default=False)
    sms_provider = Column(String, nullable=True)  # kaspi, twilio, etc.
    sms_api_key = Column(String, nullable=True)

    # Feature flags
    enable_public_catalog = Column(Boolean, default=True)
    enable_lead_management = Column(Boolean, default=True)
    enable_webhooks = Column(Boolean, default=True)
    enable_audit_log = Column(Boolean, default=True)

    # Payment settings
    require_two_stage_approval = Column(Boolean, default=True)
    auto_generate_payment_schedule = Column(Boolean, default=True)

    # Custom settings (JSON)
    custom_settings = Column(JSON, nullable=True)

    # Metadata
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<SystemSettings {self.company_name}>"


class EmailTemplate(Base):
    """Email templates for notifications"""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template info
    name = Column(String, nullable=False, unique=True, index=True)
    subject = Column(String, nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)

    # Variables
    description = Column(Text, nullable=True)
    available_variables = Column(JSON, nullable=True)  # List of available placeholders

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<EmailTemplate {self.name}>"
