from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.settings import SystemSettings, EmailTemplate
from app.schemas.settings import (
    SystemSettingsUpdate, SystemSettingsResponse,
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse
)
from app.api.deps import get_super_admin, get_admin_or_higher
from app.utils.repository import get_entity_or_404, check_unique_field
from app.utils.models import update_model_fields

router = APIRouter()


@router.get("/system", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Get system settings
    Admin or higher only
    """
    result = await db.execute(select(SystemSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings if not exists
        settings = SystemSettings(
            company_name="Property Management System",
            default_currency="KZT",
            default_late_fee_percentage="0.5",
            payment_reminder_days=3,
            contract_expiry_notice_days=30
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.put("/system", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """
    Update system settings
    Super Admin only
    """
    result = await db.execute(select(SystemSettings))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Please create settings first."
        )

    # Update fields
    settings = await update_model_fields(db, settings, settings_data)
    settings.updated_by_id = current_user.id
    await db.commit()
    await db.refresh(settings)

    return settings


# Email Templates

@router.post("/email-templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    template_data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """
    Create email template
    Super Admin only
    """
    # Check if template with this name exists
    await check_unique_field(
        db, EmailTemplate, EmailTemplate.name, template_data.name,
        error_message="Template with this name already exists"
    )

    template = EmailTemplate(
        **template_data.model_dump(),
        updated_by_id=current_user.id
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template


@router.get("/email-templates", response_model=List[EmailTemplateResponse])
async def list_email_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List all email templates"""
    query = select(EmailTemplate)

    if is_active is not None:
        query = query.where(EmailTemplate.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())

    result = await db.execute(query)
    templates = result.scalars().all()

    return templates


@router.get("/email-templates/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get email template by ID"""
    template = await get_entity_or_404(db, EmailTemplate, template_id, "Email template")
    return template


@router.get("/email-templates/by-name/{name}", response_model=EmailTemplateResponse)
async def get_email_template_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get email template by name"""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.name == name)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found"
        )

    return template


@router.put("/email-templates/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: int,
    template_data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Update email template"""
    template = await get_entity_or_404(db, EmailTemplate, template_id, "Email template")

    # Update fields
    template = await update_model_fields(db, template, template_data)
    template.updated_by_id = current_user.id
    await db.commit()
    await db.refresh(template)

    return template


@router.delete("/email-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Delete email template"""
    template = await get_entity_or_404(db, EmailTemplate, template_id, "Email template")
    await db.delete(template)
    await db.commit()

    return None
