from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from app.db.session import get_db
from app.models.property import Premise, PremiseStatus
from app.schemas.property import PremiseListResponse

router = APIRouter()


@router.get("/premises", response_model=List[PremiseListResponse])
async def get_public_premises(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    premise_type: Optional[str] = Query(None),
    min_area: Optional[float] = Query(None),
    max_area: Optional[float] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    floor: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get published premises for public catalog (no authentication required)

    Filters:
    - premise_type: office, retail, warehouse, production
    - min_area, max_area: area range in sq.m
    - min_price, max_price: price range per month
    - floor: specific floor number
    """
    query = select(Premise).where(
        Premise.is_published == True,
        Premise.status == PremiseStatus.AVAILABLE
    )

    # Apply filters
    if premise_type:
        query = query.where(Premise.premise_type == premise_type)

    if min_area:
        query = query.where(Premise.area >= min_area)

    if max_area:
        query = query.where(Premise.area <= max_area)

    if min_price:
        query = query.where(Premise.price_per_month >= min_price)

    if max_price:
        query = query.where(Premise.price_per_month <= max_price)

    if floor:
        query = query.where(Premise.floor == floor)

    # Order by featured first, then by created date
    query = query.order_by(
        Premise.is_featured.desc(),
        Premise.created_at.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    premises = result.scalars().all()
    return premises


@router.get("/premises/{premise_id}", response_model=PremiseListResponse)
async def get_public_premise(
    premise_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single premise for public catalog (increments view count)"""
    result = await db.execute(
        select(Premise).where(
            Premise.id == premise_id,
            Premise.is_published == True
        )
    )
    premise = result.scalar_one_or_none()

    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found or not published"
        )

    # Increment view count
    premise.views_count += 1
    await db.commit()
    await db.refresh(premise)

    return premise


@router.get("/search", response_model=List[PremiseListResponse])
async def search_premises(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search premises by text query"""
    search_term = f"%{q}%"

    query = select(Premise).where(
        Premise.is_published == True,
        Premise.status == PremiseStatus.AVAILABLE,
        or_(
            Premise.number.ilike(search_term),
            Premise.description.ilike(search_term)
        )
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    premises = result.scalars().all()
    return premises
