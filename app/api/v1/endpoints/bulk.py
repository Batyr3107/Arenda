from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.models.property import Premise, PremiseStatus
from app.models.payment import Payment, PaymentStatus
from app.models.notification import Notification
from app.api.deps import get_moderator_or_higher, get_admin_or_higher

router = APIRouter()


class BulkPremisePublish(BaseModel):
    premise_ids: List[int]
    is_published: bool


class BulkPremiseStatusUpdate(BaseModel):
    premise_ids: List[int]
    status: PremiseStatus


class BulkPaymentApprove(BaseModel):
    payment_ids: List[int]


class BulkNotificationMarkRead(BaseModel):
    notification_ids: List[int]


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.post("/premises/publish")
async def bulk_publish_premises(
    request: BulkPremisePublish,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Bulk publish/unpublish premises"""
    updated_count = 0

    for premise_id in request.premise_ids:
        result = await db.execute(
            select(Premise).where(Premise.id == premise_id)
        )
        premise = result.scalar_one_or_none()

        if premise:
            premise.is_published = request.is_published
            updated_count += 1

    await db.commit()

    return {
        "message": f"Updated {updated_count} premises",
        "updated_count": updated_count,
        "total_requested": len(request.premise_ids)
    }


@router.post("/premises/status")
async def bulk_update_premise_status(
    request: BulkPremiseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Bulk update premise status"""
    updated_count = 0

    for premise_id in request.premise_ids:
        result = await db.execute(
            select(Premise).where(Premise.id == premise_id)
        )
        premise = result.scalar_one_or_none()

        if premise:
            premise.status = request.status
            updated_count += 1

    await db.commit()

    return {
        "message": f"Updated {updated_count} premises to status {request.status.value}",
        "updated_count": updated_count,
        "total_requested": len(request.premise_ids)
    }


@router.post("/payments/approve-first")
async def bulk_approve_payments_first_stage(
    request: BulkPaymentApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Bulk approve payments (first stage)"""
    from datetime import date

    approved_count = 0
    failed = []

    for payment_id in request.payment_ids:
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            failed.append({"id": payment_id, "reason": "Payment not found"})
            continue

        if payment.status != PaymentStatus.PENDING_APPROVAL:
            failed.append({"id": payment_id, "reason": "Invalid status"})
            continue

        payment.first_approved_by_id = current_user.id
        payment.first_approved_at = date.today()
        approved_count += 1

    await db.commit()

    return {
        "message": f"Approved {approved_count} payments (first stage)",
        "approved_count": approved_count,
        "total_requested": len(request.payment_ids),
        "failed": failed
    }


@router.post("/payments/approve-second")
async def bulk_approve_payments_second_stage(
    request: BulkPaymentApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Bulk approve payments (second stage - final)"""
    from datetime import date

    approved_count = 0
    failed = []

    for payment_id in request.payment_ids:
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            failed.append({"id": payment_id, "reason": "Payment not found"})
            continue

        if not payment.first_approved_by_id:
            failed.append({"id": payment_id, "reason": "Not approved in first stage"})
            continue

        payment.status = PaymentStatus.APPROVED
        payment.second_approved_by_id = current_user.id
        payment.second_approved_at = date.today()
        payment.payment_date = date.today()
        approved_count += 1

    await db.commit()

    return {
        "message": f"Approved {approved_count} payments (final)",
        "approved_count": approved_count,
        "total_requested": len(request.payment_ids),
        "failed": failed
    }


@router.post("/notifications/mark-read")
async def bulk_mark_notifications_read(
    request: BulkNotificationMarkRead,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Bulk mark notifications as read"""
    updated_count = 0

    for notification_id in request.notification_ids:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            updated_count += 1

    await db.commit()

    return {
        "message": f"Marked {updated_count} notifications as read",
        "updated_count": updated_count,
        "total_requested": len(request.notification_ids)
    }


@router.delete("/notifications")
async def bulk_delete_notifications(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Bulk delete notifications"""
    deleted_count = 0

    for notification_id in request.ids:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            await db.delete(notification)
            deleted_count += 1

    await db.commit()

    return {
        "message": f"Deleted {deleted_count} notifications",
        "deleted_count": deleted_count,
        "total_requested": len(request.ids)
    }
