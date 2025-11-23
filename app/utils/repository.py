"""
Repository utilities for common database operations
Eliminates 29+ repeated get-by-ID patterns across endpoints
"""
from typing import Type, TypeVar, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.db.session import Base

T = TypeVar('T', bound=Base)


async def get_entity_or_404(
    db: AsyncSession,
    model: Type[T],
    entity_id: int,
    entity_name: Optional[str] = None,
    relations: list = None
) -> T:
    """
    Generic get-by-ID with 404 handling

    Args:
        db: Database session
        model: SQLAlchemy model class
        entity_id: ID to fetch
        entity_name: Custom name for error message
        relations: List of relationships to eager load

    Returns:
        Entity instance

    Raises:
        HTTPException: 404 if not found

    Example:
        property_obj = await get_entity_or_404(
            db, Property, property_id, "Property"
        )

        # With eager loading:
        contract = await get_entity_or_404(
            db, Contract, contract_id, "Contract",
            relations=[Contract.tenant, Contract.premise]
        )
    """
    query = select(model).where(model.id == entity_id)

    # Add eager loading if requested
    if relations:
        for relation in relations:
            query = query.options(selectinload(relation))

    result = await db.execute(query)
    entity = result.scalar_one_or_none()

    if not entity:
        name = entity_name or model.__name__
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name} not found"
        )

    return entity


async def get_entity_or_none(
    db: AsyncSession,
    model: Type[T],
    entity_id: int,
    relations: list = None
) -> Optional[T]:
    """
    Generic get-by-ID without 404

    Returns None if not found instead of raising exception
    """
    query = select(model).where(model.id == entity_id)

    if relations:
        for relation in relations:
            query = query.options(selectinload(relation))

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def check_unique_field(
    db: AsyncSession,
    model: Type[Base],
    field,
    value: Any,
    exclude_id: Optional[int] = None,
    company_id: Optional[int] = None,  # ✅ NEW
    error_message: Optional[str] = None
) -> bool:
    """
    Check if field value is unique in database

    Args:
        db: Database session
        model: SQLAlchemy model class
        field: Model field to check (e.g., User.email)
        value: Value to check for uniqueness
        exclude_id: ID to exclude from check (for updates)
        company_id: If provided and model has company_id, scope uniqueness to company
        error_message: Custom error message

    Raises:
        HTTPException: 400 if value already exists

    Returns:
        True if unique

    Example:
        await check_unique_field(
            db, Company, Company.bin_iin, "123456789",
            error_message="Company with this BIN/IIN already exists"
        )

        # For updates:
        await check_unique_field(
            db, User, User.email, new_email,
            exclude_id=user.id
        )

        # With company scope:
        await check_unique_field(
            db, Property, Property.name, "Downtown Suite",
            company_id=current_user.company_id
        )
    """
    query = select(model).where(field == value)

    if exclude_id is not None:
        query = query.where(model.id != exclude_id)

    # ✅ NEW: Scope to company if supported
    if company_id is not None and hasattr(model, 'company_id'):
        query = query.where(model.company_id == company_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        if error_message is None:
            field_name = str(field).split('.')[-1]
            error_message = f"{field_name} already exists"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    return True


async def delete_entity(
    db: AsyncSession,
    model: Type[Base],
    entity_id: int,
    entity_name: Optional[str] = None
) -> None:
    """
    Generic delete with 404 handling

    Example:
        await delete_entity(db, Property, property_id, "Property")
    """
    entity = await get_entity_or_404(db, model, entity_id, entity_name)
    await db.delete(entity)
    await db.commit()


async def soft_delete_entity(
    db: AsyncSession,
    entity: Base
) -> Base:
    """
    Soft delete entity (set is_deleted=True)

    Assumes model has is_deleted and deleted_at fields

    Example:
        contract = await get_entity_or_404(db, Contract, contract_id)
        await soft_delete_entity(db, contract)
    """
    from datetime import datetime

    entity.is_deleted = True
    entity.deleted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(entity)
    return entity
