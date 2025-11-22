from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List
from app.models.contract import Contract, PaymentSchedule, PaymentFrequency
from app.models.payment import Payment, PaymentType, PaymentStatus


async def generate_payment_schedule(db: AsyncSession, contract: Contract) -> List[PaymentSchedule]:
    """
    Generate payment schedule for contract based on payment frequency

    Returns:
        List of created payment schedules
    """
    schedules = []
    current_date = contract.start_date

    while current_date < contract.end_date:
        # Calculate next payment date based on frequency
        if contract.payment_frequency == PaymentFrequency.MONTHLY:
            # Use payment_day if specified
            payment_date = date(current_date.year, current_date.month, contract.payment_day)

            # If payment day is invalid for this month, use last day
            try:
                payment_date = date(current_date.year, current_date.month, contract.payment_day)
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30)
                payment_date = date(current_date.year, current_date.month, 1) + relativedelta(months=1) - timedelta(days=1)

            # Period is one month
            period_end = date(current_date.year, current_date.month, 1) + relativedelta(months=1) - timedelta(days=1)

        elif contract.payment_frequency == PaymentFrequency.QUARTERLY:
            payment_date = current_date
            period_end = current_date + relativedelta(months=3) - timedelta(days=1)

        else:  # YEARLY
            payment_date = current_date
            period_end = current_date + relativedelta(years=1) - timedelta(days=1)

        # Ensure period end doesn't exceed contract end
        if period_end > contract.end_date:
            period_end = contract.end_date

        # Create payment schedule
        schedule = PaymentSchedule(
            contract_id=contract.id,
            due_date=payment_date,
            amount=contract.monthly_rent,
            description=f"Аренда за {current_date.strftime('%B %Y')}"
        )
        db.add(schedule)
        schedules.append(schedule)

        # Move to next period
        if contract.payment_frequency == PaymentFrequency.MONTHLY:
            current_date = current_date + relativedelta(months=1)
        elif contract.payment_frequency == PaymentFrequency.QUARTERLY:
            current_date = current_date + relativedelta(months=3)
        else:
            current_date = current_date + relativedelta(years=1)

    await db.commit()
    return schedules


async def generate_monthly_payments(db: AsyncSession, contract: Contract) -> List[Payment]:
    """
    Generate payment records for upcoming month

    This should be run monthly to create payment records
    """
    # Get payment schedules for this month that don't have payments yet
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = month_start + relativedelta(months=1) - timedelta(days=1)

    # Find schedules
    from sqlalchemy import select, and_
    result = await db.execute(
        select(PaymentSchedule).where(
            and_(
                PaymentSchedule.contract_id == contract.id,
                PaymentSchedule.due_date >= month_start,
                PaymentSchedule.due_date <= month_end,
                PaymentSchedule.is_paid == False
            )
        )
    )
    schedules = result.scalars().all()

    payments = []
    for schedule in schedules:
        # Generate payment number
        payment_number = f"PAY-{contract.id}-{schedule.id}-{today.strftime('%Y%m%d')}"

        payment = Payment(
            contract_id=contract.id,
            payment_number=payment_number,
            payment_type=PaymentType.RENT,
            amount=schedule.amount,
            status=PaymentStatus.PENDING,
            due_date=schedule.due_date,
            period_start=month_start,
            period_end=month_end,
            description=schedule.description
        )
        db.add(payment)
        payments.append(payment)

    await db.commit()
    return payments


async def check_contract_expiry(db: AsyncSession) -> List[Contract]:
    """
    Check for contracts expiring in next 30 days

    Returns:
        List of contracts expiring soon
    """
    from sqlalchemy import and_
    today = date.today()
    expiry_threshold = today + timedelta(days=30)

    result = await db.execute(
        select(Contract).where(
            and_(
                Contract.end_date <= expiry_threshold,
                Contract.end_date >= today,
                Contract.status == "active"
            )
        )
    )

    return result.scalars().all()
