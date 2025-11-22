from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    PROPERTY_ADMIN = "property_admin"
    MODERATOR = "moderator"
    SALES_MANAGER = "sales_manager"
    TENANT = "tenant"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TENANT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    assigned_property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    company = relationship("Company", back_populates="users")
    assigned_property = relationship("Property", back_populates="assigned_users")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
