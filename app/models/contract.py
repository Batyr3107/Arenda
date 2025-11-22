from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class PaymentFrequency(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Contract(Base):
    """Договор аренды"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    premise_id = Column(Integer, ForeignKey("premises.id"), nullable=False)

    # Contract details
    contract_number = Column(String, unique=True, nullable=False, index=True)
    status = Column(SQLEnum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    signed_date = Column(Date, nullable=True)

    # Financial
    monthly_rent = Column(Float, nullable=False)  # Ежемесячная арендная плата
    deposit_amount = Column(Float, nullable=True)  # Залог
    deposit_paid = Column(Boolean, default=False)  # Залог оплачен
    deposit_paid_date = Column(Date, nullable=True)  # Дата оплаты залога
    deposit_refunded = Column(Boolean, default=False)  # Залог возвращен
    deposit_refund_amount = Column(Float, nullable=True)  # Сумма возврата залога
    deposit_refund_date = Column(Date, nullable=True)  # Дата возврата залога
    payment_frequency = Column(SQLEnum(PaymentFrequency), default=PaymentFrequency.MONTHLY)
    payment_day = Column(Integer, default=1)  # День месяца для оплаты
    late_fee_percentage = Column(Float, default=0.1)  # Процент пени за день просрочки
    currency = Column(String, default="KZT")  # Валюта

    # Additional terms
    utilities_included = Column(Boolean, default=False)  # Коммунальные услуги включены
    utilities_cost = Column(Float, nullable=True)  # Стоимость коммунальных услуг
    terms_and_conditions = Column(Text, nullable=True)
    special_conditions = Column(Text, nullable=True)

    # Renewal
    auto_renew = Column(Boolean, default=False)  # Автопродление
    renewal_notice_days = Column(Integer, default=30)  # За сколько дней уведомить о продлении
    early_termination_fee = Column(Float, nullable=True)  # Штраф за досрочное расторжение

    # Documents
    contract_file_url = Column(String, nullable=True)  # PDF договора

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="contracts")
    premise = relationship("Premise", back_populates="contracts")
    payment_schedules = relationship("PaymentSchedule", back_populates="contract", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="contract")

    def __repr__(self):
        return f"<Contract {self.contract_number}>"


class PaymentSchedule(Base):
    """График платежей по договору"""
    __tablename__ = "payment_schedules"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    # Payment details
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)  # Описание платежа
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    paid_amount = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="payment_schedules")

    def __repr__(self):
        return f"<PaymentSchedule {self.due_date} - {self.amount}>"
