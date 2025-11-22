from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"  # Ожидает подтверждения
    APPROVED = "approved"  # Подтвержден
    REJECTED = "rejected"  # Отклонен
    OVERDUE = "overdue"  # Просрочен


class PaymentType(str, enum.Enum):
    RENT = "rent"
    UTILITIES = "utilities"
    DEPOSIT = "deposit"
    PENALTY = "penalty"
    OTHER = "other"


class Payment(Base):
    """Платеж"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    # Payment details
    payment_number = Column(String, unique=True, nullable=False, index=True)
    payment_type = Column(SQLEnum(PaymentType), nullable=False, default=PaymentType.RENT)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Dates
    payment_date = Column(Date, nullable=True)  # Дата фактической оплаты
    due_date = Column(Date, nullable=False)  # Срок оплаты
    period_start = Column(Date, nullable=True)  # Начало периода
    period_end = Column(Date, nullable=True)  # Конец периода

    # Additional info
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Late fees
    late_fee = Column(Float, default=0.0)  # Пеня
    days_overdue = Column(Integer, default=0)

    # Approval workflow
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    first_approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    second_approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    first_approved_at = Column(DateTime(timezone=True), nullable=True)
    second_approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="payments")
    documents = relationship("PaymentDocument", back_populates="payment", cascade="all, delete-orphan")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    first_approved_by = relationship("User", foreign_keys=[first_approved_by_id])
    second_approved_by = relationship("User", foreign_keys=[second_approved_by_id])

    def __repr__(self):
        return f"<Payment {self.payment_number}>"


class PaymentDocument(Base):
    """Документы к платежу (чеки, квитанции и т.д.)"""
    __tablename__ = "payment_documents"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)

    # Document details
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # В байтах
    mime_type = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="documents")

    def __repr__(self):
        return f"<PaymentDocument {self.file_name}>"
