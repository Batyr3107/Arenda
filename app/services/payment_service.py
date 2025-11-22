from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from typing import List
from app.models.payment import Payment, PaymentStatus
from app.models.contract import Contract
from app.models.notification import Notification, NotificationType
from app.utils.email import send_payment_due_notification, send_payment_overdue_notification


async def calculate_late_fee(payment: Payment, contract: Contract) -> float:
    """Calculate late fee for overdue payment"""
    if not payment.due_date or payment.payment_date:
        return 0.0

    today = date.today()
    if today <= payment.due_date:
        return 0.0

    days_overdue = (today - payment.due_date).days
    late_fee = payment.amount * (contract.late_fee_percentage / 100) * days_overdue

    return round(late_fee, 2)


async def update_overdue_payments(db: AsyncSession):
    """Update status and calculate late fees for overdue payments"""
    today = date.today()

    # Get pending payments that are overdue
    result = await db.execute(
        select(Payment).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date < today
        )
    )
    overdue_payments = result.scalars().all()

    for payment in overdue_payments:
        # Get contract
        contract_result = await db.execute(
            select(Contract).where(Contract.id == payment.contract_id)
        )
        contract = contract_result.scalar_one_or_none()

        if contract:
            # Calculate days overdue and late fee
            days_overdue = (today - payment.due_date).days
            late_fee = await calculate_late_fee(payment, contract)

            # Update payment
            payment.status = PaymentStatus.OVERDUE
            payment.days_overdue = days_overdue
            payment.late_fee = late_fee

    await db.commit()


async def send_payment_reminders(db: AsyncSession):
    """Send email reminders for upcoming payments"""
    # Get payments due in 3 days
    reminder_date = date.today() + timedelta(days=3)

    result = await db.execute(
        select(Payment).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date == reminder_date
        )
    )
    upcoming_payments = result.scalars().all()

    for payment in upcoming_payments:
        # Get contract and related data
        contract_result = await db.execute(
            select(Contract).where(Contract.id == payment.contract_id)
        )
        contract = contract_result.scalar_one()

        # TODO: Get tenant email and send notification
        # await send_payment_due_notification(...)


async def approve_payment_first_stage(
    db: AsyncSession,
    payment: Payment,
    user_id: int,
    approved: bool,
    rejection_reason: str = None
) -> Payment:
    """First stage approval by moderator"""
    if payment.status != PaymentStatus.PENDING_APPROVAL:
        raise ValueError("Payment is not in pending approval status")

    if approved:
        payment.status = PaymentStatus.PENDING_APPROVAL  # Still needs second approval
        payment.first_approved_by_id = user_id
        payment.first_approved_at = date.today()
    else:
        payment.status = PaymentStatus.REJECTED
        payment.rejection_reason = rejection_reason

    await db.commit()
    await db.refresh(payment)
    return payment


async def approve_payment_second_stage(
    db: AsyncSession,
    payment: Payment,
    user_id: int,
    approved: bool,
    rejection_reason: str = None
) -> Payment:
    """Second stage approval by admin"""
    if not payment.first_approved_by_id:
        raise ValueError("Payment must be approved in first stage first")

    if approved:
        payment.status = PaymentStatus.APPROVED
        payment.second_approved_by_id = user_id
        payment.second_approved_at = date.today()
        payment.payment_date = date.today()
    else:
        payment.status = PaymentStatus.REJECTED
        payment.rejection_reason = rejection_reason

    await db.commit()
    await db.refresh(payment)
    return payment
