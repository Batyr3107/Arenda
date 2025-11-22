from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.payment import Payment
from app.models.user import User
from app.api.deps import get_moderator_or_higher

router = APIRouter()


@router.get("")
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all payments"""
    result = await db.execute(
        select(Payment)
        .offset(skip)
        .limit(limit)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return payments
