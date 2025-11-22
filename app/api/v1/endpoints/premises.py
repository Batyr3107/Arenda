from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.property import Premise
from app.models.user import User
from app.schemas.property import PremiseCreate, PremiseUpdate, PremiseResponse
from app.api.deps import get_moderator_or_higher

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
    result = await db.execute(select(Premise).where(Premise.id == premise_id))
    premise = result.scalar_one_or_none()

    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found"
        )

    return premise


@router.put("/{premise_id}", response_model=PremiseResponse)
async def update_premise(
    premise_id: int,
    premise_data: PremiseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update premise"""
    result = await db.execute(select(Premise).where(Premise.id == premise_id))
    premise = result.scalar_one_or_none()

    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found"
        )

    # Update fields
    for field, value in premise_data.model_dump(exclude_unset=True).items():
        setattr(premise, field, value)

    await db.commit()
    await db.refresh(premise)
    return premise


@router.delete("/{premise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_premise(
    premise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete premise"""
    result = await db.execute(select(Premise).where(Premise.id == premise_id))
    premise = result.scalar_one_or_none()

    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found"
        )

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
    result = await db.execute(select(Premise).where(Premise.id == premise_id))
    premise = result.scalar_one_or_none()

    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found"
        )

    premise.is_published = is_published
    await db.commit()
    await db.refresh(premise)
    return premise
