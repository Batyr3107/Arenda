import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS notification service supporting multiple providers"""

    def __init__(self):
        self.provider = settings.SMS_PROVIDER

    async def send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS message
        Returns: True if sent successfully, False otherwise
        """
        if self.provider == "twilio":
            return await self._send_via_twilio(phone, message)
        elif self.provider == "kaspi":
            return await self._send_via_kaspi(phone, message)
        else:
            logger.warning(f"Unknown SMS provider: {self.provider}")
            return False

    async def _send_via_twilio(self, phone: str, message: str) -> bool:
        """Send SMS via Twilio"""
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured")
            return False

        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            data = {
                "From": settings.TWILIO_PHONE_NUMBER,
                "To": phone,
                "Body": message
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, auth=auth, data=data, timeout=10.0)
                response.raise_for_status()

                logger.info(f"SMS sent successfully to {phone} via Twilio")
                return True

        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {e}")
            return False

    async def _send_via_kaspi(self, phone: str, message: str) -> bool:
        """Send SMS via Kaspi (Kazakhstan)"""
        if not settings.KASPI_SMS_API_KEY or not settings.KASPI_SMS_API_URL:
            logger.warning("Kaspi SMS credentials not configured")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {settings.KASPI_SMS_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "phone": phone,
                "message": message
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.KASPI_SMS_API_URL,
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                response.raise_for_status()

                logger.info(f"SMS sent successfully to {phone} via Kaspi")
                return True

        except Exception as e:
            logger.error(f"Failed to send SMS via Kaspi: {e}")
            return False

    async def send_verification_code(self, phone: str, code: str) -> bool:
        """Send verification code via SMS"""
        message = f"Ваш код подтверждения: {code}. Действителен 10 минут."
        return await self.send_sms(phone, message)

    async def send_payment_reminder(self, phone: str, amount: float, due_date: str) -> bool:
        """Send payment reminder via SMS"""
        message = f"Напоминание: платеж {amount} KZT должен быть оплачен до {due_date}."
        return await self.send_sms(phone, message)

    async def send_contract_expiry_notice(self, phone: str, contract_number: str, days_left: int) -> bool:
        """Send contract expiry notice"""
        message = f"Ваш договор №{contract_number} истекает через {days_left} дней. Пожалуйста, свяжитесь с нами."
        return await self.send_sms(phone, message)


# Singleton instance
sms_service = SMSService()
