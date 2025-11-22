from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class LeadStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CONTACTED = "contacted"
    VIEWING_SCHEDULED = "viewing_scheduled"
    VIEWED = "viewed"
    NEGOTIATION = "negotiation"
    CONTRACT_SIGNED = "contract_signed"
    REJECTED_BY_CLIENT = "rejected_by_client"
    REJECTED_BY_COMPANY = "rejected_by_company"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    WEBSITE = "website"
    PHONE = "phone"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    OTHER = "other"


class Lead(Base):
    """Заявка от потенциального клиента"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    premise_id = Column(Integer, ForeignKey("premises.id"), nullable=True)

    # Contact info
    full_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)

    # Requirements
    desired_area = Column(Float, nullable=True)  # Желаемая площадь
    budget = Column(Float, nullable=True)  # Бюджет
    lease_term = Column(String, nullable=True)  # Срок аренды
    message = Column(Text, nullable=True)  # Комментарий клиента

    # Lead management
    status = Column(SQLEnum(LeadStatus), nullable=False, default=LeadStatus.NEW)
    source = Column(SQLEnum(LeadSource), nullable=False, default=LeadSource.WEBSITE)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Ответственный менеджер
    priority = Column(Integer, default=0)  # Приоритет (0-низкий, 1-средний, 2-высокий)

    # Viewing details
    viewing_date = Column(DateTime(timezone=True), nullable=True)
    viewing_completed = Column(Boolean, default=False)

    # Rejection details
    rejection_reason = Column(Text, nullable=True)

    # GDPR
    consent_given = Column(Boolean, default=False)  # Согласие на обработку данных

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    contacted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    property = relationship("Property", back_populates="leads")
    premise = relationship("Premise", back_populates="leads")
    assigned_to = relationship("User")
    communications = relationship("LeadCommunication", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.full_name} - {self.status}>"


class LeadCommunication(Base):
    """История коммуникаций с лидом"""
    __tablename__ = "lead_communications"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто записал

    # Communication details
    communication_type = Column(String, nullable=False)  # phone, email, meeting, etc.
    subject = Column(String, nullable=True)
    notes = Column(Text, nullable=False)
    next_action = Column(String, nullable=True)
    next_action_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="communications")
    user = relationship("User")

    def __repr__(self):
        return f"<LeadCommunication {self.communication_type}>"
