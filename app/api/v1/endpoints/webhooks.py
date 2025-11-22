from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.webhook import Webhook, WebhookDelivery, WebhookEvent
from app.schemas.webhook import (
    WebhookCreate, WebhookUpdate, WebhookResponse,
    WebhookDeliveryResponse, WebhookTestRequest
)
from app.api.deps import get_admin_or_higher
from app.utils.webhook import send_webhook

router = APIRouter()


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Create new webhook endpoint
    Admin or higher only
    """
    # Convert events enum to values for storage
    events = [event.value for event in webhook_data.events]

    webhook = Webhook(
        name=webhook_data.name,
        url=str(webhook_data.url),
        description=webhook_data.description,
        events=events,
        is_active=webhook_data.is_active,
        secret=webhook_data.secret,
        custom_headers=webhook_data.custom_headers,
        created_by_id=current_user.id
    )

    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List all webhooks"""
    query = select(Webhook)

    if is_active is not None:
        query = query.where(Webhook.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(Webhook.created_at.desc())

    result = await db.execute(query)
    webhooks = result.scalars().all()

    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get webhook by ID"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Update webhook"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Update fields
    update_data = webhook_data.model_dump(exclude_unset=True)

    # Convert events enum to values
    if 'events' in update_data:
        update_data['events'] = [event.value for event in update_data['events']]

    # Convert HttpUrl to string
    if 'url' in update_data:
        update_data['url'] = str(update_data['url'])

    for field, value in update_data.items():
        setattr(webhook, field, value)

    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Delete webhook"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    await db.delete(webhook)
    await db.commit()

    return None


@router.post("/{webhook_id}/test", status_code=status.HTTP_200_OK)
async def test_webhook(
    webhook_id: int,
    test_request: WebhookTestRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Test webhook by sending a test payload
    """
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Prepare test payload
    test_payload = test_request.test_data if test_request else {
        "test": True,
        "message": "This is a test webhook delivery",
        "user_id": current_user.id
    }

    # Send test webhook using first event type
    if webhook.events:
        event_type = WebhookEvent(webhook.events[0])
        await send_webhook(
            db=db,
            event_type=event_type,
            payload=test_payload,
            webhook_id=webhook_id
        )

        await db.commit()

        return {
            "message": "Test webhook sent",
            "event_type": event_type.value,
            "payload": test_payload
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook has no events configured"
        )


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    success: bool = Query(None, description="Filter by success status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Get delivery history for a webhook
    """
    query = select(WebhookDelivery).where(
        WebhookDelivery.webhook_id == webhook_id
    )

    if success is not None:
        query = query.where(WebhookDelivery.success == success)

    query = query.order_by(desc(WebhookDelivery.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    deliveries = result.scalars().all()

    return deliveries


@router.get("/deliveries/recent", response_model=List[WebhookDeliveryResponse])
async def get_recent_deliveries(
    limit: int = Query(50, ge=1, le=200),
    success: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """
    Get recent webhook deliveries across all webhooks
    """
    query = select(WebhookDelivery)

    if success is not None:
        query = query.where(WebhookDelivery.success == success)

    query = query.order_by(desc(WebhookDelivery.created_at)).limit(limit)

    result = await db.execute(query)
    deliveries = result.scalars().all()

    return deliveries
