from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    user_id = Column(Integer, nullable=True, index=True)
    user_email = Column(String, nullable=True)

    # What action was performed
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)  # e.g., "Contract", "Payment"
    entity_id = Column(Integer, nullable=True, index=True)

    # Details
    description = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)  # Previous state
    new_values = Column(JSON, nullable=True)  # New state

    # Request info
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}#{self.entity_id} by user#{self.user_id}>"
