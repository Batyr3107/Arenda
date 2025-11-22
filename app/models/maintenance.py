from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class MaintenanceStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceCategory(str, enum.Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    STRUCTURAL = "structural"
    APPLIANCES = "appliances"
    PEST_CONTROL = "pest_control"
    CLEANING = "cleaning"
    SECURITY = "security"
    OTHER = "other"


class MaintenanceRequest(Base):
    """Maintenance request from tenants or property managers"""
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)

    # Request info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(MaintenanceCategory), nullable=False)
    priority = Column(SQLEnum(MaintenancePriority), default=MaintenancePriority.MEDIUM)
    status = Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.OPEN, index=True)

    # Location
    premise_id = Column(Integer, ForeignKey("premises.id"), nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)

    # Reporter (tenant or staff)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    actual_completion = Column(DateTime(timezone=True), nullable=True)

    # Cost tracking
    estimated_cost = Column(Integer, nullable=True)  # in cents
    actual_cost = Column(Integer, nullable=True)  # in cents

    # Access info
    requires_access = Column(Boolean, default=True)
    access_instructions = Column(Text, nullable=True)

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    premise = relationship("Premise", foreign_keys=[premise_id])
    building = relationship("Building", foreign_keys=[building_id])
    property = relationship("Property", foreign_keys=[property_id])
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    def __repr__(self):
        return f"<MaintenanceRequest {self.id} - {self.title}>"


class MaintenanceComment(Base):
    """Comments on maintenance requests"""
    __tablename__ = "maintenance_comments"

    id = Column(Integer, primary_key=True, index=True)

    maintenance_request_id = Column(Integer, ForeignKey("maintenance_requests.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes not visible to tenants

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    maintenance_request = relationship("MaintenanceRequest", backref="comments")
    user = relationship("User")

    def __repr__(self):
        return f"<MaintenanceComment {self.id}>"
