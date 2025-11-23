from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.property import Premise, Building, Property
from app.models.maintenance import MaintenanceRequest, MaintenanceComment, MaintenanceStatus, MaintenancePriority
from app.schemas.maintenance import (
    MaintenanceRequestCreate, MaintenanceRequestUpdate, MaintenanceRequestResolve,
    MaintenanceRequestResponse, MaintenanceCommentCreate, MaintenanceCommentResponse
)
from app.api.deps import get_current_user, get_moderator_or_higher
from app.utils.repository import get_entity_or_404
from app.utils.models import update_model_fields

router = APIRouter()


@router.post("", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_request(
    request_data: MaintenanceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new maintenance request"""
    # Validate premise ownership via Building→Property
    result = await db.execute(
        select(Premise).join(Building).join(Property).where(
            Premise.id == request_data.premise_id,
            Property.company_id == current_user.company_id
        )
    )
    premise = result.scalar_one_or_none()
    if not premise:
        raise HTTPException(status_code=404, detail="Premise not found or access denied")

    maintenance_request = MaintenanceRequest(
        **request_data.model_dump(),
        reported_by_id=current_user.id,
        building_id=premise.building_id,
        property_id=premise.property_id
    )

    db.add(maintenance_request)
    await db.commit()
    await db.refresh(maintenance_request)

    return maintenance_request


@router.get("", response_model=List[MaintenanceRequestResponse])
async def list_maintenance_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[MaintenanceStatus] = Query(None),
    priority: Optional[MaintenancePriority] = Query(None),
    premise_id: Optional[int] = Query(None),
    assigned_to_me: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List maintenance requests"""
    # Filter by company via premise→building→property
    query = select(MaintenanceRequest).join(Premise).join(Building).join(Property).where(
        Property.company_id == current_user.company_id
    )

    # Filters
    if status_filter:
        query = query.where(MaintenanceRequest.status == status_filter)

    if priority:
        query = query.where(MaintenanceRequest.priority == priority)

    if premise_id:
        query = query.where(MaintenanceRequest.premise_id == premise_id)

    if assigned_to_me:
        query = query.where(MaintenanceRequest.assigned_to_id == current_user.id)

    # If user is tenant, only show their requests
    if current_user.role.value == "tenant":
        query = query.where(MaintenanceRequest.reported_by_id == current_user.id)

    query = query.offset(skip).limit(limit).order_by(MaintenanceRequest.created_at.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    return requests


@router.get("/{request_id}", response_model=MaintenanceRequestResponse)
async def get_maintenance_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get maintenance request by ID"""
    # Validate ownership via building→property
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    # Check access: tenant can only see their own requests
    if current_user.role.value == "tenant" and maintenance_request.reported_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )

    return maintenance_request


@router.put("/{request_id}", response_model=MaintenanceRequestResponse)
async def update_maintenance_request(
    request_id: int,
    request_data: MaintenanceRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update maintenance request"""
    # Validate ownership
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    # Update fields
    update_data = request_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(maintenance_request, field, value)

    # If assigning, set assigned_at
    if "assigned_to_id" in update_data and update_data["assigned_to_id"]:
        maintenance_request.assigned_at = datetime.utcnow()
        if maintenance_request.status == MaintenanceStatus.OPEN:
            maintenance_request.status = MaintenanceStatus.IN_PROGRESS

    await db.commit()
    await db.refresh(maintenance_request)

    return maintenance_request


@router.post("/{request_id}/resolve", response_model=MaintenanceRequestResponse)
async def resolve_maintenance_request(
    request_id: int,
    resolve_data: MaintenanceRequestResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Resolve maintenance request"""
    # Validate ownership
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    maintenance_request.status = MaintenanceStatus.RESOLVED
    maintenance_request.resolution_notes = resolve_data.resolution_notes
    maintenance_request.resolved_by_id = current_user.id
    maintenance_request.resolved_at = datetime.utcnow()
    maintenance_request.actual_completion = datetime.utcnow()

    if resolve_data.actual_cost:
        maintenance_request.actual_cost = resolve_data.actual_cost

    await db.commit()
    await db.refresh(maintenance_request)

    return maintenance_request


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete maintenance request"""
    # Validate ownership
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    await db.delete(maintenance_request)
    await db.commit()

    return None


# Comments endpoints

@router.post("/{request_id}/comments", response_model=MaintenanceCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    request_id: int,
    comment_data: MaintenanceCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add comment to maintenance request"""
    # Validate ownership via building→property
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    comment = MaintenanceComment(
        maintenance_request_id=request_id,
        user_id=current_user.id,
        comment=comment_data.comment,
        is_internal=comment_data.is_internal
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment


@router.get("/{request_id}/comments", response_model=List[MaintenanceCommentResponse])
async def list_comments(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List comments for maintenance request"""
    # Validate ownership via building→property
    result = await db.execute(
        select(MaintenanceRequest)
        .join(Premise).join(Building).join(Property)
        .where(
            MaintenanceRequest.id == request_id,
            Property.company_id == current_user.company_id
        )
    )
    maintenance_request = result.scalar_one_or_none()
    if not maintenance_request:
        raise HTTPException(status_code=404, detail="Maintenance request not found or access denied")

    query = select(MaintenanceComment).where(
        MaintenanceComment.maintenance_request_id == request_id
    )

    # If user is tenant, don't show internal comments
    if current_user.role.value == "tenant":
        query = query.where(MaintenanceComment.is_internal == False)

    query = query.order_by(MaintenanceComment.created_at.asc())

    result = await db.execute(query)
    comments = result.scalars().all()

    return comments
