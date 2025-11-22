"""
Webhook delivery utilities
"""
import httpx
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.webhook import Webhook, WebhookDelivery, WebhookEvent

logger = logging.getLogger(__name__)


async def send_webhook(
    db: AsyncSession,
    event_type: WebhookEvent,
    payload: Dict[str, Any],
    webhook_id: Optional[int] = None
):
    """
    Send webhook notification for an event

    Args:
        db: Database session
        event_type: Type of event (e.g., PAYMENT_CREATED)
        payload: Data to send
        webhook_id: Specific webhook to send to (if None, sends to all matching webhooks)
    """
    # Get webhooks that are subscribed to this event
    query = select(Webhook).where(
        Webhook.is_active == True
    )

    if webhook_id:
        query = query.where(Webhook.id == webhook_id)

    result = await db.execute(query)
    webhooks = result.scalars().all()

    for webhook in webhooks:
        # Check if webhook is subscribed to this event
        if event_type.value not in webhook.events:
            continue

        await _deliver_webhook(db, webhook, event_type, payload)


async def _deliver_webhook(
    db: AsyncSession,
    webhook: Webhook,
    event_type: WebhookEvent,
    payload: Dict[str, Any]
):
    """
    Deliver webhook to a specific endpoint

    Args:
        db: Database session
        webhook: Webhook configuration
        event_type: Event type
        payload: Payload to send
    """
    # Prepare payload with metadata
    full_payload = {
        "event": event_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload
    }

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Arenda-Webhook/1.0"
    }

    # Add custom headers
    if webhook.custom_headers:
        headers.update(webhook.custom_headers)

    # Add signature if secret is configured
    if webhook.secret:
        signature = _generate_signature(webhook.secret, full_payload)
        headers["X-Webhook-Signature"] = signature

    # Create delivery record
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=full_payload,
        headers=headers,
        success=False
    )

    try:
        # Send webhook with timeout
        start_time = datetime.utcnow()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook.url,
                json=full_payload,
                headers=headers
            )

        end_time = datetime.utcnow()
        response_time = int((end_time - start_time).total_seconds() * 1000)

        # Update delivery record
        delivery.status_code = response.status_code
        delivery.response_body = response.text[:1000]  # Limit to 1000 chars
        delivery.response_time_ms = response_time
        delivery.success = 200 <= response.status_code < 300

        # Update webhook stats
        webhook.total_deliveries += 1
        if delivery.success:
            webhook.successful_deliveries += 1
            webhook.last_delivery_status = "success"
        else:
            webhook.failed_deliveries += 1
            webhook.last_delivery_status = f"failed: {response.status_code}"
            delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"

        webhook.last_delivery_at = datetime.utcnow()

        logger.info(
            f"Webhook delivered: {webhook.name} - {event_type.value} - "
            f"Status: {response.status_code} - Time: {response_time}ms"
        )

    except httpx.TimeoutException:
        delivery.error_message = "Request timeout (10s)"
        webhook.failed_deliveries += 1
        webhook.last_delivery_status = "timeout"
        logger.error(f"Webhook timeout: {webhook.name} - {event_type.value}")

    except httpx.RequestError as e:
        delivery.error_message = f"Request error: {str(e)}"
        webhook.failed_deliveries += 1
        webhook.last_delivery_status = "error"
        logger.error(f"Webhook error: {webhook.name} - {event_type.value} - {e}")

    except Exception as e:
        delivery.error_message = f"Unexpected error: {str(e)}"
        webhook.failed_deliveries += 1
        webhook.last_delivery_status = "error"
        logger.exception(f"Webhook unexpected error: {webhook.name} - {event_type.value}")

    # Save delivery record
    db.add(delivery)
    await db.flush()


def _generate_signature(secret: str, payload: Dict[str, Any]) -> str:
    """
    Generate HMAC signature for webhook payload

    Args:
        secret: Webhook secret
        payload: Payload to sign

    Returns:
        Hex-encoded HMAC signature
    """
    payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_signature(secret: str, payload: Dict[str, Any], signature: str) -> bool:
    """
    Verify webhook signature

    Args:
        secret: Webhook secret
        payload: Received payload
        signature: Received signature

    Returns:
        True if signature is valid
    """
    expected_signature = _generate_signature(secret, payload)
    return hmac.compare_digest(expected_signature, signature)


# Convenience functions for common events

async def notify_payment_created(db: AsyncSession, payment_id: int, payment_data: Dict[str, Any]):
    """Notify that a payment was created"""
    await send_webhook(
        db,
        WebhookEvent.PAYMENT_CREATED,
        {"payment_id": payment_id, "payment": payment_data}
    )


async def notify_payment_approved(db: AsyncSession, payment_id: int, approved_by: int):
    """Notify that a payment was approved"""
    await send_webhook(
        db,
        WebhookEvent.PAYMENT_APPROVED,
        {"payment_id": payment_id, "approved_by": approved_by}
    )


async def notify_contract_created(db: AsyncSession, contract_id: int, contract_data: Dict[str, Any]):
    """Notify that a contract was created"""
    await send_webhook(
        db,
        WebhookEvent.CONTRACT_CREATED,
        {"contract_id": contract_id, "contract": contract_data}
    )


async def notify_lead_created(db: AsyncSession, lead_id: int, lead_data: Dict[str, Any]):
    """Notify that a new lead was created"""
    await send_webhook(
        db,
        WebhookEvent.LEAD_CREATED,
        {"lead_id": lead_id, "lead": lead_data}
    )
