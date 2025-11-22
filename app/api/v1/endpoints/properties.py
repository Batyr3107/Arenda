from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.property import Property, Building
from app.models.user import User
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse,
    BuildingCreate, BuildingUpdate, BuildingResponse
)
from app.api.deps import get_moderator_or_higher

router = APIRouter()


# Property endpoints
@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new property (requires moderator or higher)"""
    property_obj = Property(**property_data.model_dump())
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    return property_obj


@router.get("", response_model=List[PropertyResponse])
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all properties"""
    result = await db.execute(
        select(Property)
        .offset(skip)
        .limit(limit)
        .order_by(Property.created_at.desc())
    )
    properties = result.scalars().all()
    return properties


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get property by ID"""
    result = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    return property_obj


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update property"""
    result = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Update fields
    for field, value in property_data.model_dump(exclude_unset=True).items():
        setattr(property_obj, field, value)

    await db.commit()
    await db.refresh(property_obj)
    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete property"""
    result = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    await db.delete(property_obj)
    await db.commit()


# Building endpoints
@router.post("/{property_id}/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    property_id: int,
    building_data: BuildingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new building in property"""
    # Verify property exists
    result = await db.execute(select(Property).where(Property.id == property_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    building = Building(**building_data.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return building


@router.get("/{property_id}/buildings", response_model=List[BuildingResponse])
async def list_buildings(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all buildings in property"""
    result = await db.execute(
        select(Building)
        .where(Building.property_id == property_id)
        .order_by(Building.name)
    )
    buildings = result.scalars().all()
    return buildings
