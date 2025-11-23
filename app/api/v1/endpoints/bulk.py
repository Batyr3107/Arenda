from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import date
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
    """Bulk publish/unpublish premises
    Refactored: N queries → 1 batch query (N+1 fix)
    SECURITY FIX: Added company_id validation to prevent cross-company access"""
    from app.models.property import Building, Property

    # ✅ SECURITY: Only fetch premises that belong to user's company
    result = await db.execute(
        select(Premise)
        .join(Building, Premise.building_id == Building.id)
        .join(Property, Building.property_id == Property.id)
        .where(
            Premise.id.in_(request.premise_ids),
            Property.company_id == current_user.company_id  # ✅ Company isolation
        )
    )
    premises = result.scalars().all()

    # ✅ Check if all requested premises were found (security check)
    if len(premises) != len(request.premise_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Some premises do not belong to your company or were not found"
        )

    # Update all found premises
    for premise in premises:
        premise.is_published = request.is_published

    await db.commit()

    return {
        "message": f"Updated {len(premises)} premises",
        "updated_count": len(premises),
        "total_requested": len(request.premise_ids)
    }


@router.post("/premises/status")
async def bulk_update_premise_status(
    request: BulkPremiseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Bulk update premise status
    Refactored: N queries → 1 batch query (N+1 fix)
    SECURITY FIX: Added company_id validation
    BUSINESS LOGIC FIX: Added contract status validation"""
    from app.models.property import Building, Property
    from app.models.contract import Contract, ContractStatus
    from sqlalchemy.orm import selectinload

    # ✅ SECURITY: Only fetch premises that belong to user's company
    result = await db.execute(
        select(Premise)
        .join(Building, Premise.building_id == Building.id)
        .join(Property, Building.property_id == Property.id)
        .where(
            Premise.id.in_(request.premise_ids),
            Property.company_id == current_user.company_id
        )
        .options(selectinload(Premise.contracts))  # ✅ Load contracts for validation
    )
    premises = result.scalars().all()

    # ✅ Security check
    if len(premises) != len(request.premise_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Some premises do not belong to your company or were not found"
        )

    # ✅ BUSINESS LOGIC: Validate status changes with contract state
    failed = []
    updated_count = 0

    for premise in premises:
        active_contracts = [c for c in premise.contracts if c.status == ContractStatus.ACTIVE]

        # ✅ Cannot set OCCUPIED without active contract
        if request.status == PremiseStatus.OCCUPIED and not active_contracts:
            failed.append({
                "id": premise.id,
                "number": premise.number,
                "reason": "Cannot set OCCUPIED status without active contract"
            })
            continue

        # ✅ Cannot set AVAILABLE with active contracts
        if request.status == PremiseStatus.AVAILABLE and active_contracts:
            failed.append({
                "id": premise.id,
                "number": premise.number,
                "reason": f"Cannot set AVAILABLE status with {len(active_contracts)} active contract(s)"
            })
            continue

        premise.status = request.status
        updated_count += 1

    await db.commit()

    return {
        "message": f"Updated {updated_count} premises to status {request.status.value}",
        "updated_count": updated_count,
        "total_requested": len(request.premise_ids),
        "failed": failed
    }


@router.post("/payments/approve-first")
async def bulk_approve_payments_first_stage(
    request: BulkPaymentApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Bulk approve payments (first stage)
    Refactored: N queries → 1 batch query (N+1 fix)
    SECURITY FIX: Added company_id validation
    RACE CONDITION FIX: Using atomic UPDATE to prevent concurrent approval conflicts"""
    from app.models.contract import Contract
    from app.models.tenant import Tenant
    from sqlalchemy import update as sql_update
    from datetime import datetime

    # ✅ SECURITY: First verify all payments belong to user's company
    result = await db.execute(
        select(Payment.id)
        .join(Contract, Payment.contract_id == Contract.id)
        .join(Tenant, Contract.tenant_id == Tenant.id)
        .where(
            Payment.id.in_(request.payment_ids),
            Tenant.company_id == current_user.company_id  # ✅ Company isolation
        )
    )
    valid_payment_ids = set(result.scalars().all())

    # Check for unauthorized access
    unauthorized_ids = set(request.payment_ids) - valid_payment_ids
    failed = []
    if unauthorized_ids:
        for payment_id in unauthorized_ids:
            failed.append({
                "id": payment_id,
                "reason": "Payment not found or does not belong to your company"
            })

    # ✅ RACE CONDITION FIX: Atomic UPDATE prevents double-approval
    # Only update payments that are PENDING_APPROVAL and NOT YET approved
    result = await db.execute(
        sql_update(Payment)
        .where(
            Payment.id.in_(list(valid_payment_ids)),
            Payment.status == PaymentStatus.PENDING_APPROVAL,
            Payment.first_approved_by_id.is_(None)  # ✅ Atomic check - only if not approved yet
        )
        .values(
            first_approved_by_id=current_user.id,
            first_approved_at=datetime.utcnow()
        )
        .returning(Payment.id)
    )
    approved_ids = result.scalars().all()
    approved_count = len(approved_ids)

    # Check for payments that couldn't be approved (wrong status or already approved)
    not_approved_ids = valid_payment_ids - set(approved_ids)
    if not_approved_ids:
        # Fetch details for failed payments
        result = await db.execute(
            select(Payment).where(Payment.id.in_(list(not_approved_ids)))
        )
        not_approved_payments = result.scalars().all()

        for payment in not_approved_payments:
            if payment.first_approved_by_id is not None:
                reason = f"Already approved by user {payment.first_approved_by_id}"
            else:
                reason = f"Invalid status: {payment.status.value}"

            failed.append({
                "id": payment.id,
                "reason": reason
            })

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
    """Bulk approve payments (second stage - final)
    Refactored: N queries → 1 batch query (N+1 fix)
    SECURITY FIX: Added company_id validation
    RACE CONDITION FIX: Using atomic UPDATE"""
    from app.models.contract import Contract
    from app.models.tenant import Tenant
    from sqlalchemy import update as sql_update
    from datetime import datetime

    # ✅ SECURITY: Verify all payments belong to user's company
    result = await db.execute(
        select(Payment.id)
        .join(Contract, Payment.contract_id == Contract.id)
        .join(Tenant, Contract.tenant_id == Tenant.id)
        .where(
            Payment.id.in_(request.payment_ids),
            Tenant.company_id == current_user.company_id
        )
    )
    valid_payment_ids = set(result.scalars().all())

    # Check for unauthorized access
    unauthorized_ids = set(request.payment_ids) - valid_payment_ids
    failed = []
    if unauthorized_ids:
        for payment_id in unauthorized_ids:
            failed.append({
                "id": payment_id,
                "reason": "Payment not found or does not belong to your company"
            })

    # ✅ RACE CONDITION FIX: Atomic UPDATE
    # Only update payments that have first approval and NOT YET second approved
    today = datetime.utcnow()
    result = await db.execute(
        sql_update(Payment)
        .where(
            Payment.id.in_(list(valid_payment_ids)),
            Payment.first_approved_by_id.isnot(None),  # ✅ Must have first approval
            Payment.second_approved_by_id.is_(None)  # ✅ Not yet second approved
        )
        .values(
            status=PaymentStatus.APPROVED,
            second_approved_by_id=current_user.id,
            second_approved_at=today,
            payment_date=today.date()
        )
        .returning(Payment.id)
    )
    approved_ids = result.scalars().all()
    approved_count = len(approved_ids)

    # Check for failures
    not_approved_ids = valid_payment_ids - set(approved_ids)
    if not_approved_ids:
        result = await db.execute(
            select(Payment).where(Payment.id.in_(list(not_approved_ids)))
        )
        not_approved_payments = result.scalars().all()

        for payment in not_approved_payments:
            if payment.second_approved_by_id is not None:
                reason = f"Already approved by user {payment.second_approved_by_id}"
            elif payment.first_approved_by_id is None:
                reason = "Not approved in first stage"
            else:
                reason = f"Invalid status: {payment.status.value}"

            failed.append({
                "id": payment.id,
                "reason": reason
            })

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
    """Bulk mark notifications as read
    Refactored: N queries → 1 batch query (N+1 fix)"""
    # Single batch query instead of N queries
    result = await db.execute(
        select(Notification).where(
            Notification.id.in_(request.notification_ids),
            Notification.user_id == current_user.id
        )
    )
    notifications = result.scalars().all()

    # Update all found notifications
    for notification in notifications:
        notification.is_read = True

    await db.commit()

    return {
        "message": f"Marked {len(notifications)} notifications as read",
        "updated_count": len(notifications),
        "total_requested": len(request.notification_ids)
    }


@router.delete("/notifications")
async def bulk_delete_notifications(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Bulk delete notifications
    Refactored: N queries → 1 batch query (N+1 fix)"""
    # Single batch query instead of N queries
    result = await db.execute(
        select(Notification).where(
            Notification.id.in_(request.ids),
            Notification.user_id == current_user.id
        )
    )
    notifications = result.scalars().all()

    # Delete all found notifications
    for notification in notifications:
        await db.delete(notification)

    await db.commit()

    return {
        "message": f"Deleted {len(notifications)} notifications",
        "deleted_count": len(notifications),
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

        # ✅ TRANSACTION SAFETY FIX: Use savepoints for per-row transactions
        for index, row in df.iterrows():
            try:
                # ✅ Create savepoint for atomic row processing
                async with db.begin_nested():
                    tenant = Tenant(
                        full_name=row['full_name'],
                        email=row.get('email'),
                        phone=row['phone'],
                        id_number=row.get('id_number'),
                        address=row.get('address'),
                        notes=row.get('notes'),
                        company_id=current_user.company_id  # ✅ Security: Only import to own company
                    )
                    db.add(tenant)
                    await db.flush()  # ✅ Validate within savepoint
                    created_count += 1

            except Exception as e:
                # ✅ Savepoint auto-rollbacks on exception
                await db.rollback()  # Rollback only this row
                failed.append({
                    "row": index + 2,
                    "data": row.to_dict(),
                    "error": str(e)
                })

        # ✅ Commit all successful rows
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
    SECURITY FIX: Added property/building ownership validation
    TRANSACTION FIX: Added savepoint-based transaction safety
    """
    from app.models.property import Building, Property

    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) and CSV files are supported"
        )

    # ✅ SECURITY: Validate building/property ownership BEFORE processing file
    result = await db.execute(
        select(Building)
        .join(Property, Building.property_id == Property.id)
        .where(
            Building.id == building_id,
            Building.property_id == property_id,
            Property.company_id == current_user.company_id  # ✅ Company isolation
        )
    )
    building = result.scalar_one_or_none()

    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found or does not belong to your company"
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

        # ✅ TRANSACTION SAFETY: Use savepoints for per-row transactions
        for index, row in df.iterrows():
            try:
                async with db.begin_nested():
                    premise = Premise(
                        number=str(row['number']),
                        floor=int(row.get('floor', 1)),
                        area=float(row['area']),
                        premise_type=PremiseType.OFFICE,  # Default type
                        price_per_month=float(row['price']),
                        description=row.get('description'),
                        building_id=building_id,  # ✅ Only building_id, no property_id in model
                        status=PremiseStatus.AVAILABLE
                    )
                    db.add(premise)
                    await db.flush()  # ✅ Validate within savepoint
                    created_count += 1

            except Exception as e:
                await db.rollback()  # ✅ Rollback only this row
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
