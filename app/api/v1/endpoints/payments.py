from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date
from app.db.session import get_db
from app.models.payment import Payment, PaymentDocument, PaymentStatus
from app.models.contract import Contract
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentDetailResponse,
    PaymentApprovalRequest, PaymentDocumentResponse
)
from app.api.deps import get_moderator_or_higher, get_admin_or_higher, get_current_active_user
from app.services.payment_service import approve_payment_first_stage, approve_payment_second_stage
from app.services.payment_invoice_service import prepare_invoice_pdf_data
from app.utils.file_upload import save_payment_document
from app.utils.pdf_generator import create_invoice_pdf, create_payment_act_pdf
from app.utils.repository import get_entity_or_404
from app.utils.models import update_model_fields

router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """Create new payment"""
    payment = Payment(**payment_data.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: PaymentStatus = Query(None),
    contract_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all payments with filters"""
    query = select(Payment)

    if status:
        query = query.where(Payment.status == status)

    if contract_id:
        query = query.where(Payment.contract_id == contract_id)

    query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()
    return payments


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment by ID with documents"""
    payment = await get_entity_or_404(
        db, Payment, payment_id, "Payment",
        relations=[Payment.documents]
    )
    return payment


@router.post("/{payment_id}/upload-document", response_model=PaymentDocumentResponse)
async def upload_payment_document(
    payment_id: int,
    file: UploadFile = File(...),
    description: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload payment document (for tenants)"""
    # Verify payment exists
    payment = await get_entity_or_404(db, Payment, payment_id, "Payment")

    # Save file
    file_url, file_size = await save_payment_document(file)

    # Create document record
    document = PaymentDocument(
        payment_id=payment_id,
        file_url=file_url,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        description=description
    )
    db.add(document)

    # Update payment status to pending approval
    if payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.PENDING_APPROVAL
        payment.uploaded_by_id = current_user.id

    await db.commit()
    await db.refresh(document)
    return document


@router.post("/{payment_id}/approve-first", response_model=PaymentResponse)
async def approve_payment_first(
    payment_id: int,
    approval_data: PaymentApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """First stage approval by moderator"""
    payment = await get_entity_or_404(db, Payment, payment_id, "Payment")

    payment = await approve_payment_first_stage(
        db, payment, current_user.id, approval_data.approved, approval_data.rejection_reason
    )

    return payment


@router.post("/{payment_id}/approve-second", response_model=PaymentResponse)
async def approve_payment_second(
    payment_id: int,
    approval_data: PaymentApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Second stage approval by admin"""
    payment = await get_entity_or_404(db, Payment, payment_id, "Payment")

    payment = await approve_payment_second_stage(
        db, payment, current_user.id, approval_data.approved, approval_data.rejection_reason
    )

    return payment


@router.get("/{payment_id}/invoice-pdf")
async def download_invoice_pdf(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate and download invoice PDF
    Refactored: 48 lines → 11 lines, completed 3 TODOs"""
    pdf_data = await prepare_invoice_pdf_data(db, payment_id)
    pdf_buffer = create_invoice_pdf(**pdf_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{pdf_data['invoice_number']}.pdf"
        }
    )


@router.get("/overdue/list", response_model=List[PaymentResponse])
async def list_overdue_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """List all overdue payments"""
    result = await db.execute(
        select(Payment)
        .where(Payment.status == PaymentStatus.OVERDUE)
        .offset(skip)
        .limit(limit)
        .order_by(Payment.due_date)
    )
    payments = result.scalars().all()
    return payments
