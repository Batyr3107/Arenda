from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.api.deps import get_super_admin
from app.utils.repository import get_entity_or_404, check_unique_field
from app.utils.models import update_model_fields

router = APIRouter()


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Create new company (Super Admin only)"""
    # Check if company with this BIN/IIN already exists
    await check_unique_field(
        db, Company, Company.bin_iin, company_data.bin_iin,
        error_message="Company with this BIN/IIN already exists"
    )

    company = Company(**company_data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Search by name, legal_name, or BIN/IIN"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """List all companies with optional search (Super Admin only)"""
    query = select(Company)

    if search:
        query = query.where(
            or_(
                Company.name.ilike(f"%{search}%"),
                Company.legal_name.ilike(f"%{search}%"),
                Company.bin_iin.ilike(f"%{search}%")
            )
        )

    query = query.offset(skip).limit(limit).order_by(Company.created_at.desc())

    result = await db.execute(query)
    companies = result.scalars().all()
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Get company by ID (Super Admin only)"""
    company = await get_entity_or_404(db, Company, company_id, "Company")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Update company (Super Admin only)"""
    company = await get_entity_or_404(db, Company, company_id, "Company")

    # Check if BIN/IIN is being changed and if it's already taken
    if company_data.bin_iin and company_data.bin_iin != company.bin_iin:
        await check_unique_field(
            db, Company, Company.bin_iin, company_data.bin_iin,
            exclude_id=company_id,
            error_message="Company with this BIN/IIN already exists"
        )

    company = await update_model_fields(db, company, company_data)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Delete company (Super Admin only)"""
    company = await get_entity_or_404(db, Company, company_id, "Company")
    await db.delete(company)
    await db.commit()
