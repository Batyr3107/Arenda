from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_db
from app.models.tenant import Tenant, TenantContact
from app.models.user import User
from app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantResponse, TenantDetailResponse,
    TenantContactCreate, TenantContactUpdate, TenantContactResponse
)
from app.api.deps import get_moderator_or_higher
from app.utils.repository import get_entity_or_404, check_unique_field
from app.utils.models import update_model_fields

router = APIRouter()


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new tenant"""
    # Check if tenant with same BIN/IIN exists
    if tenant_data.bin_iin:
        await check_unique_field(
            db, Tenant, Tenant.bin_iin, tenant_data.bin_iin,
            error_message="Tenant with this BIN/IIN already exists"
        )

    tenant = Tenant(**tenant_data.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all tenants with optional filters"""
    query = select(Tenant)

    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Tenant.name.ilike(search_term)) |
            (Tenant.email.ilike(search_term)) |
            (Tenant.phone.ilike(search_term))
        )

    query = query.offset(skip).limit(limit).order_by(Tenant.created_at.desc())

    result = await db.execute(query)
    tenants = result.scalars().all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get tenant by ID with contacts"""
    tenant = await get_entity_or_404(
        db, Tenant, tenant_id, "Tenant",
        relations=[Tenant.contacts]
    )
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update tenant"""
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")
    tenant = await update_model_fields(db, tenant, tenant_data)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete tenant"""
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")
    await db.delete(tenant)
    await db.commit()


# Tenant Contacts
@router.post("/{tenant_id}/contacts", response_model=TenantContactResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_contact(
    tenant_id: int,
    contact_data: TenantContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Add contact to tenant"""
    # Verify tenant exists
    await get_entity_or_404(db, Tenant, tenant_id, "Tenant")

    contact = TenantContact(tenant_id=tenant_id, **contact_data.model_dump(exclude={'tenant_id'}))
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{tenant_id}/contacts", response_model=List[TenantContactResponse])
async def list_tenant_contacts(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get all contacts for a tenant"""
    result = await db.execute(
        select(TenantContact)
        .where(TenantContact.tenant_id == tenant_id)
        .order_by(TenantContact.is_primary.desc(), TenantContact.created_at)
    )
    contacts = result.scalars().all()
    return contacts


@router.put("/contacts/{contact_id}", response_model=TenantContactResponse)
async def update_tenant_contact(
    contact_id: int,
    contact_data: TenantContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update tenant contact"""
    contact = await get_entity_or_404(db, TenantContact, contact_id, "Contact")
    contact = await update_model_fields(db, contact, contact_data)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete tenant contact"""
    contact = await get_entity_or_404(db, TenantContact, contact_id, "Contact")
    await db.delete(contact)
    await db.commit()
