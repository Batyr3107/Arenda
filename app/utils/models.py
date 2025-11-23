"""
Model manipulation utilities
Eliminates 11+ repeated model update patterns
"""
from typing import TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import Base

T = TypeVar('T', bound=Base)


async def update_model_fields(
    db: AsyncSession,
    model: T,
    update_data: BaseModel,
    exclude_fields: set = None
) -> T:
    """
    Update model with Pydantic schema data

    Args:
        db: Database session
        model: Model instance to update
        update_data: Pydantic model with updated data
        exclude_fields: Set of field names to exclude from update

    Returns:
        Updated model instance

    Example:
        property_obj = await get_entity_or_404(db, Property, property_id)
        property_obj = await update_model_fields(
            db, property_obj, property_data
        )
        return property_obj

        # With exclusions:
        user = await update_model_fields(
            db, user, user_data,
            exclude_fields={'password'}  # Don't update password this way
        )
    """
    exclude_fields = exclude_fields or set()

    # Get only fields that were actually provided
    update_dict = update_data.model_dump(exclude_unset=True)

    # Apply updates
    for field, value in update_dict.items():
        if field not in exclude_fields and hasattr(model, field):
            setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return model


async def create_model_from_schema(
    db: AsyncSession,
    model_class: Type[T],
    create_data: BaseModel,
    **additional_fields
) -> T:
    """
    Create model instance from Pydantic schema

    Args:
        db: Database session
        model_class: SQLAlchemy model class to instantiate
        create_data: Pydantic model with creation data
        **additional_fields: Additional fields to add (e.g., user_id, company_id)

    Returns:
        Created model instance

    Example:
        property_obj = await create_model_from_schema(
            db, Property, property_data,
            company_id=current_user.company_id
        )
        return property_obj
    """
    # Merge schema data with additional fields
    data = create_data.model_dump()
    data.update(additional_fields)

    # Create instance
    instance = model_class(**data)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    return instance


def model_to_dict(model: Base, exclude_fields: set = None) -> dict:
    """
    Convert SQLAlchemy model to dictionary

    Args:
        model: Model instance
        exclude_fields: Fields to exclude from dictionary

    Returns:
        Dictionary representation

    Example:
        user_dict = model_to_dict(user, exclude_fields={'hashed_password'})
    """
    exclude_fields = exclude_fields or set()

    result = {}
    for column in model.__table__.columns:
        if column.name not in exclude_fields:
            result[column.name] = getattr(model, column.name)

    return result


async def clone_model(
    db: AsyncSession,
    model: T,
    exclude_fields: set = None,
    override_fields: dict = None
) -> T:
    """
    Clone a model instance with optional field overrides

    Args:
        db: Database session
        model: Model to clone
        exclude_fields: Fields to exclude (usually 'id')
        override_fields: Fields to override in clone

    Returns:
        New model instance

    Example:
        # Clone contract for renewal
        new_contract = await clone_model(
            db, old_contract,
            exclude_fields={'id', 'created_at'},
            override_fields={
                'contract_number': generate_new_number(),
                'start_date': new_start_date,
                'end_date': new_end_date
            }
        )
    """
    exclude_fields = exclude_fields or {'id', 'created_at', 'updated_at'}
    override_fields = override_fields or {}

    # Get model data
    data = model_to_dict(model, exclude_fields=exclude_fields)

    # Apply overrides
    data.update(override_fields)

    # Create new instance
    new_instance = type(model)(**data)
    db.add(new_instance)
    await db.commit()
    await db.refresh(new_instance)

    return new_instance


async def bulk_create_models(
    db: AsyncSession,
    model_class: Type[T],
    data_list: list[dict]
) -> list[T]:
    """
    Bulk create multiple model instances

    Args:
        db: Database session
        model_class: Model class to create
        data_list: List of dictionaries with model data

    Returns:
        List of created instances

    Example:
        premises = await bulk_create_models(
            db, Premise,
            [
                {'number': '101', 'area': 50, 'property_id': 1},
                {'number': '102', 'area': 60, 'property_id': 1}
            ]
        )
    """
    instances = [model_class(**data) for data in data_list]
    db.add_all(instances)
    await db.commit()

    # Refresh all instances
    for instance in instances:
        await db.refresh(instance)

    return instances
