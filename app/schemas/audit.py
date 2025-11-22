from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    action: AuditAction
    entity_type: str
    entity_id: Optional[int]
    description: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
