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
    """Create new tenant
    SECURITY FIX: Enforces company_id from current user"""
    # Check if tenant with same BIN/IIN exists in THIS company
    if tenant_data.bin_iin:
        await check_unique_field(
            db, Tenant, Tenant.bin_iin, tenant_data.bin_iin,
            error_message="Tenant with this BIN/IIN already exists"
            # TODO: Add company_id scope when HIGH-1 is fixed
        )

    # ✅ SECURITY: Force company_id from current user, ignore any value from request
    tenant_dict = tenant_data.model_dump(exclude={'company_id'})
    tenant = Tenant(**tenant_dict, company_id=current_user.company_id)
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
    """List all tenants with optional filters
    SECURITY FIX: Only shows tenants from current user's company"""
    # ✅ SECURITY: Always filter by company_id
    query = select(Tenant).where(Tenant.company_id == current_user.company_id)

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
    """Get tenant by ID with contacts
    SECURITY FIX: Validates tenant ownership"""
    tenant = await get_entity_or_404(
        db, Tenant, tenant_id, "Tenant",
        relations=[Tenant.contacts]
    )

    # ✅ SECURITY: Verify tenant belongs to user's company
    if tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update tenant
    SECURITY FIX: Validates tenant ownership"""
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    tenant = await update_model_fields(db, tenant, tenant_data)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete tenant
    SECURITY FIX: Validates tenant ownership"""
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

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
    """Add contact to tenant
    CRITICAL FIX: Added tenant ownership validation"""
    # Verify tenant exists and belongs to user's company
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

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
    """Get all contacts for a tenant
    CRITICAL FIX: Added tenant ownership validation"""
    # Verify tenant exists and belongs to user's company
    tenant = await get_entity_or_404(db, Tenant, tenant_id, "Tenant")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

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
    """Update tenant contact
    CRITICAL FIX: Added tenant ownership validation via contact relationship"""
    # Load contact with tenant relationship
    result = await db.execute(
        select(TenantContact)
        .options(selectinload(TenantContact.tenant))
        .where(TenantContact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if contact.tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    contact = await update_model_fields(db, contact, contact_data)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Delete tenant contact
    CRITICAL FIX: Added tenant ownership validation via contact relationship"""
    # Load contact with tenant relationship
    result = await db.execute(
        select(TenantContact)
        .options(selectinload(TenantContact.tenant))
        .where(TenantContact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # ✅ SECURITY: Verify tenant belongs to user's company
    if contact.tenant.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    await db.delete(contact)
    await db.commit()
