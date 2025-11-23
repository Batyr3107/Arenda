"""
Payment invoice PDF service
Completes the 3 TODO items in payments.py:200,204,206
Fixes incomplete invoice PDF implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.payment import Payment
from app.models.contract import Contract
from app.models.tenant import Tenant
from app.models.property import Premise
from app.services.property_service import get_system_settings
from datetime import date
from typing import Dict, Any


async def prepare_invoice_pdf_data(
    db: AsyncSession,
    payment_id: int
) -> Dict[str, Any]:
    """
    Prepare all data for invoice PDF generation

    Completes TODOs from payments.py:
    - Line 200: Get tenant and premise data
    - Line 204: Get tenant name from contract.tenant
    - Line 206: Get premise number from contract.premise

    Uses eager loading to prevent N+1 queries
    Separates data preparation from PDF generation (SRP)

    Returns:
        Dictionary with all invoice parameters

    Example:
        data = await prepare_invoice_pdf_data(db, payment_id)
        pdf_buffer = create_invoice_pdf(**data)
    """
    # Eager load ALL relationships in one query (prevents N+1)
    result = await db.execute(
        select(Payment)
        .options(
            selectinload(Payment.contract)
            .selectinload(Contract.tenant),
            selectinload(Payment.contract)
            .selectinload(Contract.premise)
        )
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    # Get system settings for company info
    settings = await get_system_settings(db)

    # Extract data from relationships (TODOs fixed!)
    contract = payment.contract
    tenant = contract.tenant  # TODO line 204 fixed
    premise = contract.premise  # TODO line 206 fixed

    # Prepare complete invoice data
    return {
        'contract_number': contract.contract_number,
        'tenant_name': tenant.full_name,  # Was: "Tenant Name" TODO
        'tenant_address': tenant.address or "Address not specified",  # Was hardcoded
        'tenant_phone': tenant.phone,
        'premise_number': premise.number,  # Was: "123" TODO
        'premise_address': _build_premise_short_address(premise),
        'amount': payment.amount,
        'currency': payment.currency or contract.currency or 'KZT',
        'period_start': payment.period_start,
        'period_end': payment.period_end,
        'company_name': settings.company_name,
        'company_address': getattr(settings, 'company_address', 'Company address not set'),
        'company_phone': getattr(settings, 'company_phone', ''),
        'company_bank': getattr(settings, 'bank_name', 'Bank details not set'),
        'company_account': getattr(settings, 'bank_account', ''),
        'company_bin': getattr(settings, 'company_bin', ''),
        'invoice_number': payment.payment_number,
        'invoice_date': date.today(),
        'due_date': payment.due_date,
        'late_fee': payment.late_fee if payment.late_fee > 0 else None
    }


def _build_premise_short_address(premise: Premise) -> str:
    """
    Build short address for premise (without property/building details)

    Used for invoice - just premise identification
    """
    return f"Premise {premise.number}, Floor {premise.floor}"


async def get_payment_with_full_details(
    db: AsyncSession,
    payment_id: int
) -> Payment:
    """
    Get payment with all relationships eager loaded

    Prevents N+1 queries
    Single query loads: payment, contract, tenant, premise

    Example:
        payment = await get_payment_with_full_details(db, payment_id)
        # Now payment.contract.tenant, payment.contract.premise are loaded
    """
    result = await db.execute(
        select(Payment)
        .options(
            selectinload(Payment.contract)
            .selectinload(Contract.tenant),
            selectinload(Payment.contract)
            .selectinload(Contract.premise)
        )
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    return payment


async def calculate_total_with_late_fee(payment: Payment) -> float:
    """
    Calculate total payment amount including late fees

    Business logic for payment total calculation
    """
    total = payment.amount

    if payment.late_fee and payment.late_fee > 0:
        total += payment.late_fee

    return total


async def get_payment_status_display(payment: Payment) -> str:
    """
    Get human-readable payment status

    Business logic for status display
    """
    status_map = {
        'pending': 'Ожидает оплаты',
        'pending_approval': 'На проверке',
        'approved': 'Подтвержден',
        'rejected': 'Отклонен',
        'overdue': 'Просрочен'
    }

    return status_map.get(payment.status.value, payment.status.value)
