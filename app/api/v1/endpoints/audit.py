from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from datetime import date
from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.audit import AuditLogResponse
from app.api.deps import get_admin_or_higher

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: int = Query(None, description="Filter by user ID"),
    action: AuditAction = Query(None, description="Filter by action type"),
    entity_type: str = Query(None, description="Filter by entity type"),
    entity_id: int = Query(None, description="Filter by entity ID"),
    date_from: date = Query(None, description="Filter from date"),
    date_to: date = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Get audit logs with filters
    Only accessible by admins and above
    """
    query = select(AuditLog)

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)

    if date_from:
        query = query.where(AuditLog.created_at >= date_from)

    if date_to:
        from datetime import datetime, timedelta
        # Include the entire day
        date_to_end = datetime.combine(date_to, datetime.max.time())
        query = query.where(AuditLog.created_at <= date_to_end)

    # Order and paginate
    query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return logs


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get specific audit log entry"""
    result = await db.execute(
        select(AuditLog).where(AuditLog.id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    return log


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Get complete audit trail for a specific entity
    Shows all changes made to this entity over time
    """
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        )
        .order_by(desc(AuditLog.created_at))
    )
    logs = result.scalars().all()

    return logs
