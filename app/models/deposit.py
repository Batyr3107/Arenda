from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class DeductionReason(str, enum.Enum):
    DAMAGES = "damages"
    CLEANING = "cleaning"
    UNPAID_RENT = "unpaid_rent"
    LATE_FEES = "late_fees"
    UTILITIES = "utilities"
    OTHER = "other"


class DepositDeduction(Base):
    """Вычеты из залога"""
    __tablename__ = "deposit_deductions"

    id = Column(Integer, primary_key=True, index=True)

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Deduction details
    amount = Column(Float, nullable=False)  # Сумма вычета
    reason = Column(SQLEnum(DeductionReason), nullable=False)
    description = Column(Text, nullable=False)  # Описание вычета
    evidence_file_url = Column(String, nullable=True)  # Файл-доказательство (фото повреждений и т.д.)

    # Approval
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contract = relationship("Contract")
    tenant = relationship("Tenant")
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<DepositDeduction {self.id} - {self.amount}>"


class PartialPayment(Base):
    """Частичные платежи"""
    __tablename__ = "partial_payments"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)

    # Payment details
    amount = Column(Float, nullable=False)  # Сумма частичного платежа
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=True)  # Способ оплаты
    transaction_reference = Column(String, nullable=True)  # Номер транзакции
    notes = Column(Text, nullable=True)

    # Processing
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="partial_payments")
    processed_by = relationship("User", foreign_keys=[processed_by_id])

    def __repr__(self):
        return f"<PartialPayment {self.id} - {self.amount}>"
