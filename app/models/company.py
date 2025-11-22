from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    legal_name = Column(String, nullable=False)
    bin_iin = Column(String, unique=True, nullable=False, index=True)  # БИН/ИИН
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Bank details
    bank_name = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    bik = Column(String, nullable=True)  # БИК банка

    # Contact person
    director_name = Column(String, nullable=True)
    accountant_name = Column(String, nullable=True)
    accountant_phone = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="company", cascade="all, delete-orphan")
    tenants = relationship("Tenant", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name}>"
