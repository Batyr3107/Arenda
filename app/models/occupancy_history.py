from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from app.models.property import PremiseStatus


class OccupancyHistory(Base):
    """Track premise occupancy status changes over time"""
    __tablename__ = "occupancy_history"

    id = Column(Integer, primary_key=True, index=True)

    premise_id = Column(Integer, ForeignKey("premises.id"), nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)

    # Status change
    status = Column(SQLEnum(PremiseStatus), nullable=False)
    previous_status = Column(SQLEnum(PremiseStatus), nullable=True)

    # Tenant info (if occupied)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True, index=True)

    # Date tracking
    effective_date = Column(Date, nullable=False, index=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    premise = relationship("Premise", foreign_keys=[premise_id])
    building = relationship("Building", foreign_keys=[building_id])
    property = relationship("Property", foreign_keys=[property_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    changed_by = relationship("User", foreign_keys=[changed_by_id])

    def __repr__(self):
        return f"<OccupancyHistory {self.id} - Premise {self.premise_id}: {self.status}>"
