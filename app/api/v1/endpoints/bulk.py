from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.models.property import Premise, PremiseStatus
from app.models.payment import Payment, PaymentStatus
from app.models.notification import Notification
from app.models.tenant import Tenant
from app.api.deps import get_moderator_or_higher, get_admin_or_higher
import pandas as pd
import io
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


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


# ==================== BULK IMPORT ====================


@router.post("/import/tenants")
async def import_tenants_from_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Import tenants from Excel/CSV file
    Expected columns: full_name, email, phone, id_number, address, notes
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) and CSV files are supported"
        )

    try:
        contents = await file.read()

        # Read file based on type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        required_columns = ['full_name', 'phone']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        created_count = 0
        failed = []

        for index, row in df.iterrows():
            try:
                tenant = Tenant(
                    full_name=row['full_name'],
                    email=row.get('email'),
                    phone=row['phone'],
                    id_number=row.get('id_number'),
                    address=row.get('address'),
                    notes=row.get('notes'),
                    company_id=current_user.company_id
                )
                db.add(tenant)
                created_count += 1

            except Exception as e:
                failed.append({
                    "row": index + 2,
                    "data": row.to_dict(),
                    "error": str(e)
                })

        await db.commit()

        return {
            "message": f"Imported {created_count} tenants",
            "created_count": created_count,
            "total_rows": len(df),
            "failed": failed
        }

    except Exception as e:
        logger.error(f"Error importing tenants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/import/premises")
async def import_premises_from_file(
    property_id: int,
    building_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Import premises from Excel/CSV file
    Expected columns: number, floor, area, rooms, price, description
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) and CSV files are supported"
        )

    try:
        contents = await file.read()

        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        required_columns = ['number', 'area', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        created_count = 0
        failed = []

        for index, row in df.iterrows():
            try:
                premise = Premise(
                    number=str(row['number']),
                    floor=int(row.get('floor', 1)),
                    area=float(row['area']),
                    rooms=int(row.get('rooms', 1)),
                    price=float(row['price']),
                    description=row.get('description'),
                    property_id=property_id,
                    building_id=building_id,
                    status=PremiseStatus.VACANT
                )
                db.add(premise)
                created_count += 1

            except Exception as e:
                failed.append({
                    "row": index + 2,
                    "data": row.to_dict(),
                    "error": str(e)
                })

        await db.commit()

        return {
            "message": f"Imported {created_count} premises",
            "created_count": created_count,
            "total_rows": len(df),
            "failed": failed
        }

    except Exception as e:
        logger.error(f"Error importing premises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/import/template/{entity_type}")
async def download_import_template(
    entity_type: str,
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Download import template for entity type
    Available types: tenants, premises, payments
    """
    from fastapi.responses import StreamingResponse

    templates = {
        "tenants": {
            "columns": ["full_name", "email", "phone", "id_number", "address", "notes"],
            "sample": [
                ["Иванов Иван Иванович", "ivanov@example.com", "+77001234567", "123456789012", "г. Алматы, ул. Примерная 1", "VIP клиент"]
            ]
        },
        "premises": {
            "columns": ["number", "floor", "area", "rooms", "price", "description"],
            "sample": [
                ["101", 1, 45.5, 2, 150000, "2-комнатная квартира"],
                ["102", 1, 32.0, 1, 100000, "1-комнатная квартира"]
            ]
        },
        "payments": {
            "columns": ["contract_number", "amount", "due_date", "description"],
            "sample": [
                ["CNT-2024-001", 150000, "2024-12-01", "Арендная плата за декабрь"]
            ]
        }
    }

    if entity_type not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found for: {entity_type}"
        )

    template = templates[entity_type]

    # Create DataFrame
    df = pd.DataFrame(template["sample"], columns=template["columns"])

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=entity_type.capitalize())

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=import_template_{entity_type}.xlsx"
        }
    )
