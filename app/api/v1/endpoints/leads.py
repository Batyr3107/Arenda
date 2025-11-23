from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.lead import Lead, LeadCommunication
from app.models.user import User
from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse,
    LeadCommunicationCreate, LeadCommunicationResponse
)
from app.api.deps import get_moderator_or_higher
from app.utils.repository import get_entity_or_404

router = APIRouter()


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new lead (public endpoint, no auth required)"""
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    # TODO: Send notification to sales managers

    return lead


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    assigned_to_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all leads with filters"""
    query = select(Lead)

    if status:
        query = query.where(Lead.status == status)

    if assigned_to_id:
        query = query.where(Lead.assigned_to_id == assigned_to_id)

    query = query.offset(skip).limit(limit).order_by(Lead.created_at.desc())

    result = await db.execute(query)
    leads = result.scalars().all()
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get lead by ID"""
    lead = await get_entity_or_404(db, Lead, lead_id, "Lead")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update lead status and details"""
    lead = await get_entity_or_404(db, Lead, lead_id, "Lead")

    # Update fields
    for field, value in lead_data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    # Update contacted_at if status changed to contacted
    if lead_data.status and lead.contacted_at is None:
        lead.contacted_at = datetime.utcnow()

    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/{lead_id}/communications", response_model=LeadCommunicationResponse)
async def add_communication(
    lead_id: int,
    communication_data: LeadCommunicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Add communication record to lead"""
    # Verify lead exists
    await get_entity_or_404(db, Lead, lead_id, "Lead")

    communication = LeadCommunication(
        lead_id=lead_id,
        user_id=current_user.id,
        **communication_data.model_dump()
    )

    db.add(communication)
    await db.commit()
    await db.refresh(communication)
    return communication


@router.get("/{lead_id}/communications", response_model=List[LeadCommunicationResponse])
async def get_communications(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get all communications for a lead"""
    result = await db.execute(
        select(LeadCommunication)
        .where(LeadCommunication.lead_id == lead_id)
        .order_by(LeadCommunication.created_at.desc())
    )
    communications = result.scalars().all()
    return communications
