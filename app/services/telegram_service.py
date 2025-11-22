import httpx
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from app.models.telegram import TelegramUser, TelegramMessage
from app.models.user import User
from app.models.payment import Payment, PaymentStatus
from app.models.contract import Contract
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Service for interacting with Telegram Bot API"""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None
    ) -> bool:
        """Send message to telegram user"""
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send telegram message: {e}")
            return False

    async def set_webhook(self, webhook_url: str) -> bool:
        """Set telegram webhook URL"""
        if not self.bot_token:
            return False

        url = f"{self.base_url}/setWebhook"
        payload = {"url": webhook_url}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False

    async def delete_webhook(self) -> bool:
        """Delete telegram webhook"""
        if not self.bot_token:
            return False

        url = f"{self.base_url}/deleteWebhook"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, timeout=10.0)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False


async def get_or_create_telegram_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> TelegramUser:
    """Get or create telegram user"""
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
    )
    telegram_user = result.scalar_one_or_none()

    if not telegram_user:
        telegram_user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(telegram_user)
        await db.commit()
        await db.refresh(telegram_user)
    else:
        # Update info if changed
        if username:
            telegram_user.username = username
        if first_name:
            telegram_user.first_name = first_name
        if last_name:
            telegram_user.last_name = last_name
        telegram_user.last_interaction = datetime.utcnow()
        await db.commit()

    return telegram_user


async def log_telegram_message(
    db: AsyncSession,
    telegram_user_id: int,
    message_type: str,
    message_text: Optional[str] = None,
    command: Optional[str] = None,
    is_successful: bool = True,
    error_message: Optional[str] = None
):
    """Log telegram message"""
    message = TelegramMessage(
        telegram_user_id=telegram_user_id,
        message_type=message_type,
        message_text=message_text,
        command=command,
        is_successful=is_successful,
        error_message=error_message
    )
    db.add(message)
    await db.commit()


async def handle_start_command(
    db: AsyncSession,
    telegram_user: TelegramUser,
    bot_service: TelegramBotService
) -> str:
    """Handle /start command"""
    if telegram_user.user_id:
        user_result = await db.execute(
            select(User).where(User.id == telegram_user.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            return f"""
🏢 <b>Добро пожаловать в Систему Управления Арендой!</b>

Вы успешно подключены к системе как: <b>{user.full_name}</b>

<b>Доступные команды:</b>
/payments - Мои платежи
/contracts - Мои договоры
/notifications - Настройки уведомлений
/help - Справка

📊 Получайте уведомления о:
• Новых платежах
• Приближающихся сроках оплаты
• Истекающих договорах
• Важных обновлениях
            """

    return """
🏢 <b>Добро пожаловать в Систему Управления Арендой!</b>

Для начала работы необходимо связать ваш Telegram аккаунт с системой.

<b>Как подключиться:</b>
1. Войдите в систему через веб-интерфейс
2. Перейдите в раздел "Настройки"
3. Получите код верификации
4. Отправьте команду: /link ВАШ_КОД

После подключения вы сможете:
• Просматривать платежи и договоры
• Получать уведомления
• Следить за балансом

❓ /help - Помощь
    """


async def handle_payments_command(
    db: AsyncSession,
    telegram_user: TelegramUser,
    bot_service: TelegramBotService
) -> str:
    """Handle /payments command"""
    if not telegram_user.user_id:
        return "❌ Сначала подключите аккаунт командой /link"

    # Get user's contracts
    user_result = await db.execute(
        select(User).where(User.id == telegram_user.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        return "❌ Пользователь не найден"

    # Get payments for user's contracts
    contracts_result = await db.execute(
        select(Contract).where(Contract.tenant_id == user.tenant_id)
    )
    contracts = contracts_result.scalars().all()

    if not contracts:
        return "📋 У вас пока нет договоров"

    # Get recent payments
    contract_ids = [c.id for c in contracts]
    payments_result = await db.execute(
        select(Payment)
        .where(Payment.contract_id.in_(contract_ids))
        .order_by(Payment.due_date.desc())
        .limit(5)
    )
    payments = payments_result.scalars().all()

    if not payments:
        return "💳 Платежей не найдено"

    message = "💳 <b>Ваши последние платежи:</b>\n\n"

    for payment in payments:
        status_emoji = {
            PaymentStatus.PENDING: "⏳",
            PaymentStatus.APPROVED: "✅",
            PaymentStatus.PAID: "💰",
            PaymentStatus.OVERDUE: "⚠️",
            PaymentStatus.CANCELLED: "❌"
        }.get(payment.status, "❓")

        message += f"{status_emoji} <b>{payment.amount} {payment.currency}</b>\n"
        message += f"   Срок: {payment.due_date.strftime('%d.%m.%Y')}\n"
        message += f"   Статус: {payment.status.value}\n\n"

    return message


async def handle_contracts_command(
    db: AsyncSession,
    telegram_user: TelegramUser,
    bot_service: TelegramBotService
) -> str:
    """Handle /contracts command"""
    if not telegram_user.user_id:
        return "❌ Сначала подключите аккаунт командой /link"

    user_result = await db.execute(
        select(User).where(User.id == telegram_user.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.tenant_id:
        return "📋 У вас нет активных договоров"

    contracts_result = await db.execute(
        select(Contract)
        .where(Contract.tenant_id == user.tenant_id)
        .order_by(Contract.start_date.desc())
    )
    contracts = contracts_result.scalars().all()

    if not contracts:
        return "📋 Договоров не найдено"

    message = "📋 <b>Ваши договоры:</b>\n\n"

    for contract in contracts:
        status_emoji = "✅" if contract.is_active else "❌"
        message += f"{status_emoji} Договор №{contract.number}\n"
        message += f"   Период: {contract.start_date.strftime('%d.%m.%Y')} - {contract.end_date.strftime('%d.%m.%Y')}\n"
        message += f"   Аренда: {contract.monthly_rent} {contract.currency}/мес\n\n"

    return message


async def handle_notifications_command(
    db: AsyncSession,
    telegram_user: TelegramUser,
    bot_service: TelegramBotService
) -> str:
    """Handle /notifications command"""
    if not telegram_user.user_id:
        return "❌ Сначала подключите аккаунт командой /link"

    current_status = "включены" if telegram_user.is_notifications_enabled else "выключены"

    return f"""
🔔 <b>Настройки уведомлений</b>

Текущий статус: <b>{current_status}</b>

Для изменения настроек используйте команды:
/notifications_on - Включить уведомления
/notifications_off - Выключить уведомления

Вы будете получать уведомления о:
• Новых платежах
• Приближающихся сроках оплаты (за 3 дня)
• Истекающих договорах (за 30 дней)
• Важных изменениях в системе
    """


async def handle_help_command(
    db: AsyncSession,
    telegram_user: TelegramUser,
    bot_service: TelegramBotService
) -> str:
    """Handle /help command"""
    return """
ℹ️ <b>Справка по командам бота</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку

<b>Для арендаторов:</b>
/payments - Показать последние платежи
/contracts - Показать договоры
/notifications - Настройки уведомлений

<b>Подключение аккаунта:</b>
/link КОД - Связать Telegram с аккаунтом

<b>Настройки:</b>
/notifications_on - Включить уведомления
/notifications_off - Выключить уведомления

📞 Поддержка: support@arenda.kz
    """


async def send_notification_to_user(
    db: AsyncSession,
    user_id: int,
    message: str,
    bot_service: TelegramBotService
) -> bool:
    """Send notification to user via telegram"""
    result = await db.execute(
        select(TelegramUser).where(
            and_(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True,
                TelegramUser.is_notifications_enabled == True
            )
        )
    )
    telegram_user = result.scalar_one_or_none()

    if not telegram_user:
        logger.info(f"No active telegram account for user {user_id}")
        return False

    success = await bot_service.send_message(
        chat_id=telegram_user.telegram_id,
        text=message
    )

    await log_telegram_message(
        db=db,
        telegram_user_id=telegram_user.id,
        message_type="outgoing",
        message_text=message,
        is_successful=success
    )

    return success
