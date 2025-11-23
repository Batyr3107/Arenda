"""
Property business logic service
Separates business logic from endpoint handlers (SRP, DIP)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.property import Property, Building, Premise
from app.models.settings import SystemSettings
from app.schemas.property import PropertyCreate, PropertyUpdate
from app.utils.repository import get_entity_or_404, check_unique_field
from app.utils.models import update_model_fields, create_model_from_schema


async def create_property(
    db: AsyncSession,
    property_data: PropertyCreate,
    company_id: int
) -> Property:
    """
    Create new property with validation

    Business logic:
    - Validates company exists
    - Creates property
    - Sets company ownership
    """
    property_obj = await create_model_from_schema(
        db, Property, property_data,
        company_id=company_id
    )

    return property_obj


async def update_property(
    db: AsyncSession,
    property_id: int,
    property_data: PropertyUpdate
) -> Property:
    """
    Update property with validation

    Business logic:
    - Validates property exists
    - Updates fields
    - Preserves ownership
    """
    property_obj = await get_entity_or_404(db, Property, property_id, "Property")
    property_obj = await update_model_fields(db, property_obj, property_data)

    return property_obj


async def get_property_full_address(
    db: AsyncSession,
    property_id: int,
    building_id: int = None,
    premise_number: str = None
) -> str:
    """
    Build full address from property, building, and premise

    Returns: "Property Address, Building Name, Premise Number"

    Example:
        address = await get_property_full_address(
            db, property_id=1, building_id=2, premise_number="101"
        )
        # Returns: "г. Алматы, ул. Абая 150, Building A, Premise 101"
    """
    address_parts = []

    # Get property
    property_obj = await get_entity_or_404(db, Property, property_id)
    if property_obj.address:
        address_parts.append(property_obj.address)

    # Get building if provided
    if building_id:
        building = await get_entity_or_404(db, Building, building_id)
        if building.name:
            address_parts.append(f"Building {building.name}")

    # Add premise number if provided
    if premise_number:
        address_parts.append(f"Premise {premise_number}")

    return ", ".join(address_parts)


async def get_system_settings(db: AsyncSession) -> SystemSettings:
    """
    Get system settings or return defaults

    Returns:
        SystemSettings instance with defaults if not found
    """
    result = await db.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Return default settings
        settings = SystemSettings(
            company_name="Property Management Company",
            default_currency="KZT"
        )

    return settings
