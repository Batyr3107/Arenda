from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date
from app.db.session import get_db
from app.models.contract import Contract, PaymentSchedule, ContractStatus
from app.models.tenant import Tenant
from app.models.property import Premise, Building, Property
from app.models.user import User
from app.models.settings import SystemSettings
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractResponse, ContractDetailResponse,
    PaymentScheduleResponse
)
from app.api.deps import get_moderator_or_higher
from app.services.contract_service import generate_payment_schedule
from app.services.contract_pdf_service import prepare_contract_pdf_data
from app.utils.pdf_generator import create_contract_pdf
from app.utils.repository import get_entity_or_404
from app.utils.models import update_model_fields, create_model_from_schema

router = APIRouter()


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new contract and generate payment schedule"""
    # Verify tenant exists
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == contract_data.tenant_id))
    if not tenant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Verify premise exists and is available
    premise_result = await db.execute(select(Premise).where(Premise.id == contract_data.premise_id))
    premise = premise_result.scalar_one_or_none()
    if not premise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premise not found"
        )

    # Create contract
    contract = Contract(**contract_data.model_dump())
    db.add(contract)
    await db.flush()

    # Generate payment schedule
    await generate_payment_schedule(db, contract)

    # Mark premise as occupied if contract is active
    if contract.status == ContractStatus.ACTIVE:
        premise.status = "occupied"

    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("", response_model=List[ContractResponse])
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: ContractStatus = Query(None),
    tenant_id: int = Query(None),
    premise_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all contracts with filters"""
    query = select(Contract)

    if status:
        query = query.where(Contract.status == status)

    if tenant_id:
        query = query.where(Contract.tenant_id == tenant_id)

    if premise_id:
        query = query.where(Contract.premise_id == premise_id)

    query = query.offset(skip).limit(limit).order_by(Contract.created_at.desc())

    result = await db.execute(query)
    contracts = result.scalars().all()
    return contracts


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get contract by ID with payment schedules"""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.payment_schedules))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Update contract"""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Update fields
    for field, value in contract_data.model_dump(exclude_unset=True).items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.patch("/{contract_id}/activate", response_model=ContractResponse)
async def activate_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Activate contract and mark premise as occupied"""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    contract.status = ContractStatus.ACTIVE

    # Mark premise as occupied
    premise_result = await db.execute(select(Premise).where(Premise.id == contract.premise_id))
    premise = premise_result.scalar_one()
    premise.status = "occupied"

    await db.commit()
    await db.refresh(contract)
    return contract


@router.patch("/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Terminate contract and free up premise"""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    contract.status = ContractStatus.TERMINATED

    # Mark premise as available
    premise_result = await db.execute(select(Premise).where(Premise.id == contract.premise_id))
    premise = premise_result.scalar_one()
    premise.status = "available"

    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("/{contract_id}/pdf")
async def download_contract_pdf(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Generate and download contract PDF

    Refactored: 73 lines → 11 lines
    Business logic moved to contract_pdf_service (SRP, KISS)
    """
    # Prepare PDF data (all business logic in service layer)
    pdf_data = await prepare_contract_pdf_data(db, contract_id)

    # Generate PDF
    pdf_buffer = create_contract_pdf(**pdf_data)

    # Return PDF as download
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=contract_{pdf_data['contract_number']}.pdf"
        }
    )


@router.get("/{contract_id}/payment-schedules", response_model=List[PaymentScheduleResponse])
async def get_payment_schedules(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Get payment schedules for contract"""
    result = await db.execute(
        select(PaymentSchedule)
        .where(PaymentSchedule.contract_id == contract_id)
        .order_by(PaymentSchedule.due_date)
    )
    schedules = result.scalars().all()
    return schedules
