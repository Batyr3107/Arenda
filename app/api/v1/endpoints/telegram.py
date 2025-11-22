from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.telegram import TelegramUser, TelegramMessage
from app.schemas.telegram import (
    TelegramUserResponse, TelegramUserUpdate,
    TelegramLinkRequest, TelegramNotificationRequest, TelegramWebhookUpdate
)
from app.api.deps import get_current_user, get_admin_or_higher
from app.services.telegram_service import (
    TelegramBotService, get_or_create_telegram_user, log_telegram_message,
    handle_start_command, handle_payments_command, handle_contracts_command,
    handle_notifications_command, handle_help_command, send_notification_to_user
)
import secrets
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(
    update: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Telegram webhook endpoint
    Receives updates from Telegram Bot API
    """
    try:
        bot_service = TelegramBotService()

        # Extract message from update
        message = update.get("message")
        if not message:
            return {"ok": True}

        # Get user info
        from_user = message.get("from", {})
        telegram_id = from_user.get("id")
        username = from_user.get("username")
        first_name = from_user.get("first_name")
        last_name = from_user.get("last_name")
        text = message.get("text", "")

        if not telegram_id:
            return {"ok": True}

        # Get or create telegram user
        telegram_user = await get_or_create_telegram_user(
            db=db,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        # Handle commands
        response_text = ""

        if text.startswith("/start"):
            response_text = await handle_start_command(db, telegram_user, bot_service)
            await log_telegram_message(db, telegram_user.id, "incoming", text, "start")

        elif text.startswith("/help"):
            response_text = await handle_help_command(db, telegram_user, bot_service)
            await log_telegram_message(db, telegram_user.id, "incoming", text, "help")

        elif text.startswith("/payments"):
            response_text = await handle_payments_command(db, telegram_user, bot_service)
            await log_telegram_message(db, telegram_user.id, "incoming", text, "payments")

        elif text.startswith("/contracts"):
            response_text = await handle_contracts_command(db, telegram_user, bot_service)
            await log_telegram_message(db, telegram_user.id, "incoming", text, "contracts")

        elif text.startswith("/notifications"):
            if text == "/notifications_on":
                telegram_user.is_notifications_enabled = True
                await db.commit()
                response_text = "✅ Уведомления включены"
            elif text == "/notifications_off":
                telegram_user.is_notifications_enabled = False
                await db.commit()
                response_text = "🔕 Уведомления выключены"
            else:
                response_text = await handle_notifications_command(db, telegram_user, bot_service)
            await log_telegram_message(db, telegram_user.id, "incoming", text, "notifications")

        elif text.startswith("/link"):
            parts = text.split()
            if len(parts) != 2:
                response_text = "❌ Использование: /link ВАШ_КОД\n\nПолучите код в веб-интерфейсе системы."
            else:
                code = parts[1]
                # Here we would verify the code and link the account
                # For now, simple response
                response_text = f"🔗 Код получен: {code}\n\nФункция привязки аккаунта будет доступна через веб-интерфейс."
            await log_telegram_message(db, telegram_user.id, "incoming", text, "link")

        else:
            response_text = "❓ Неизвестная команда. Используйте /help для списка команд."
            await log_telegram_message(db, telegram_user.id, "incoming", text, None)

        # Send response
        if response_text:
            await bot_service.send_message(
                chat_id=telegram_id,
                text=response_text
            )
            await log_telegram_message(db, telegram_user.id, "outgoing", response_text)

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing telegram webhook: {e}")
        return {"ok": False, "error": str(e)}


@router.post("/set-webhook")
async def set_telegram_webhook(
    webhook_url: str = Query(..., description="Webhook URL"),
    current_user: User = Depends(get_admin_or_higher),
    db: AsyncSession = Depends(get_db)
):
    """
    Set Telegram webhook URL
    Admin only
    """
    bot_service = TelegramBotService()
    success = await bot_service.set_webhook(webhook_url)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set webhook"
        )

    return {"status": "success", "webhook_url": webhook_url}


@router.delete("/webhook")
async def delete_telegram_webhook(
    current_user: User = Depends(get_admin_or_higher),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete Telegram webhook
    Admin only
    """
    bot_service = TelegramBotService()
    success = await bot_service.delete_webhook()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook"
        )

    return {"status": "success"}


@router.get("/me", response_model=TelegramUserResponse)
async def get_my_telegram_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's telegram account"""
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.user_id == current_user.id)
    )
    telegram_user = result.scalar_one_or_none()

    if not telegram_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram account not linked"
        )

    return telegram_user


@router.put("/me", response_model=TelegramUserResponse)
async def update_my_telegram_settings(
    settings: TelegramUserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update telegram settings"""
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.user_id == current_user.id)
    )
    telegram_user = result.scalar_one_or_none()

    if not telegram_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram account not linked"
        )

    for field, value in settings.model_dump(exclude_unset=True).items():
        setattr(telegram_user, field, value)

    await db.commit()
    await db.refresh(telegram_user)

    return telegram_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_telegram_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlink telegram account"""
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.user_id == current_user.id)
    )
    telegram_user = result.scalar_one_or_none()

    if not telegram_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram account not linked"
        )

    telegram_user.user_id = None
    telegram_user.is_active = False
    await db.commit()

    return None


@router.post("/send-notification")
async def send_telegram_notification(
    notification: TelegramNotificationRequest,
    current_user: User = Depends(get_admin_or_higher),
    db: AsyncSession = Depends(get_db)
):
    """
    Send notification to user via telegram
    Admin only
    """
    bot_service = TelegramBotService()
    success = await send_notification_to_user(
        db=db,
        user_id=notification.user_id,
        message=notification.message,
        bot_service=bot_service
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send notification. User may not have active telegram account."
        )

    return {"status": "sent", "user_id": notification.user_id}


@router.get("/users", response_model=List[TelegramUserResponse])
async def list_telegram_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List telegram users (Admin only)"""
    query = select(TelegramUser)

    if is_active is not None:
        query = query.where(TelegramUser.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(TelegramUser.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return users


@router.get("/messages")
async def list_telegram_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    telegram_user_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List telegram messages (Admin only)"""
    query = select(TelegramMessage)

    if telegram_user_id:
        query = query.where(TelegramMessage.telegram_user_id == telegram_user_id)

    query = query.offset(skip).limit(limit).order_by(TelegramMessage.created_at.desc())

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "telegram_user_id": msg.telegram_user_id,
            "message_type": msg.message_type,
            "message_text": msg.message_text,
            "command": msg.command,
            "created_at": msg.created_at
        }
        for msg in messages
    ]
