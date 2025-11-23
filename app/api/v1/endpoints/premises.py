from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.property import Premise
from app.models.user import User
from app.schemas.property import PremiseCreate, PremiseUpdate, PremiseResponse
from app.api.deps import get_moderator_or_higher
from app.utils.repository import get_entity_or_404
from app.utils.models import update_model_fields

router = APIRouter()


@router.post("", response_model=PremiseResponse, status_code=status.HTTP_201_CREATED)
async def create_premise(
    premise_data: PremiseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new premise"""
    premise = Premise(**premise_data.model_dump())
    db.add(premise)
    await db.commit()
    await db.refresh(premise)
    return premise


@router.get("", response_model=List[PremiseResponse])
async def list_premises(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    building_id: int = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all premises with filters"""
    query = select(Premise)

    if building_id:
        query = query.where(Premise.building_id == building_id)

    if status:
        query = query.where(Premise.status == status)

    query = query.offset(skip).limit(limit).order_by(Premise.created_at.desc())

    result = await db.execute(query)
    premises = result.scalars().all()
    return premises


@router.get("/{premise_id}", response_model=PremiseResponse)
async def get_premise(
    premise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get premise by ID"""
    premise = await get_entity_or_404(db, Premise, premise_id, "Premise")
    return premise


@router.put("/{premise_id}", response_model=PremiseResponse)
async def update_premise(
    premise_id: int,
    premise_data: PremiseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update premise"""
    premise = await get_entity_or_404(db, Premise, premise_id, "Premise")
    premise = await update_model_fields(db, premise, premise_data)
    return premise


@router.delete("/{premise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_premise(
    premise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete premise"""
    premise = await get_entity_or_404(db, Premise, premise_id, "Premise")
    await db.delete(premise)
    await db.commit()


@router.patch("/{premise_id}/publish", response_model=PremiseResponse)
async def publish_premise(
    premise_id: int,
    is_published: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Publish or unpublish premise to public catalog"""
    premise = await get_entity_or_404(db, Premise, premise_id, "Premise")
    premise.is_published = is_published
    await db.commit()
    await db.refresh(premise)
    return premise
