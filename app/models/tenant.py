from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Tenant(Base):
    """Арендатор (компания или физлицо)"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # Basic info
    name = Column(String, nullable=False, index=True)  # Название компании или ФИО
    legal_name = Column(String, nullable=True)  # Юридическое название
    bin_iin = Column(String, index=True, nullable=True)  # БИН/ИИН
    is_individual = Column(Boolean, default=False)  # Физлицо или юрлицо

    # Contact info
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Bank details (optional)
    bank_name = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    bik = Column(String, nullable=True)

    # Additional info
    business_type = Column(String, nullable=True)  # Вид деятельности
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="tenants")
    contacts = relationship("TenantContact", back_populates="tenant", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name}>"


class TenantContact(Base):
    """Контактное лицо арендатора"""
    __tablename__ = "tenant_contacts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    # Contact info
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=True)  # Должность
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)  # Основной контакт

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="contacts")

    def __repr__(self):
        return f"<TenantContact {self.full_name}>"
