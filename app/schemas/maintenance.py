from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.maintenance import MaintenanceStatus, MaintenancePriority, MaintenanceCategory


class MaintenanceRequestCreate(BaseModel):
    title: str
    description: str
    category: MaintenanceCategory
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    premise_id: int
    requires_access: bool = True
    access_instructions: Optional[str] = None
    tenant_id: Optional[int] = None


class MaintenanceRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[MaintenanceCategory] = None
    priority: Optional[MaintenancePriority] = None
    status: Optional[MaintenanceStatus] = None
    assigned_to_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    estimated_cost: Optional[int] = None
    actual_cost: Optional[int] = None
    access_instructions: Optional[str] = None


class MaintenanceRequestResolve(BaseModel):
    resolution_notes: str
    actual_cost: Optional[int] = None


class MaintenanceRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    category: MaintenanceCategory
    priority: MaintenancePriority
    status: MaintenanceStatus
    premise_id: int
    building_id: Optional[int]
    property_id: Optional[int]
    reported_by_id: int
    tenant_id: Optional[int]
    assigned_to_id: Optional[int]
    assigned_at: Optional[datetime]
    scheduled_date: Optional[datetime]
    estimated_completion: Optional[datetime]
    actual_completion: Optional[datetime]
    estimated_cost: Optional[int]
    actual_cost: Optional[int]
    requires_access: bool
    access_instructions: Optional[str]
    resolution_notes: Optional[str]
    resolved_by_id: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MaintenanceCommentCreate(BaseModel):
    comment: str
    is_internal: bool = False


class MaintenanceCommentResponse(BaseModel):
    id: int
    maintenance_request_id: int
    user_id: int
    comment: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True
