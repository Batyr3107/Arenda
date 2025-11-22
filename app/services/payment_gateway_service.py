import httpx
import logging
import hashlib
import json
from typing import Optional, Dict, Any
from decimal import Decimal
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentGatewayService:
    """Payment gateway service supporting Stripe and Kaspi"""

    def __init__(self):
        self.provider = "stripe"  # Default provider

    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        payment_id: int,
        description: str,
        customer_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create payment intent
        Returns: payment intent data with client_secret
        """
        if not settings.ENABLE_ONLINE_PAYMENTS:
            logger.warning("Online payments are disabled")
            return None

        if settings.STRIPE_API_KEY:
            return await self._create_stripe_payment(amount, currency, payment_id, description, customer_email)
        elif settings.KASPI_PAYMENT_API_KEY:
            return await self._create_kaspi_payment(amount, currency, payment_id, description, customer_email)
        else:
            logger.error("No payment gateway configured")
            return None

    async def _create_stripe_payment(
        self,
        amount: float,
        currency: str,
        payment_id: int,
        description: str,
        customer_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe payment intent"""
        try:
            url = "https://api.stripe.com/v1/payment_intents"

            # Stripe requires amount in smallest currency unit (cents for USD, tiyn for KZT)
            stripe_amount = int(amount * 100)

            headers = {
                "Authorization": f"Bearer {settings.STRIPE_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "amount": stripe_amount,
                "currency": currency.lower(),
                "description": description,
                "metadata[payment_id]": str(payment_id)
            }

            if customer_email:
                data["receipt_email"] = customer_email

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data, timeout=10.0)
                response.raise_for_status()

                result = response.json()

                logger.info(f"Stripe payment intent created: {result['id']}")

                return {
                    "provider": "stripe",
                    "payment_intent_id": result["id"],
                    "client_secret": result["client_secret"],
                    "amount": amount,
                    "currency": currency,
                    "status": result["status"]
                }

        except Exception as e:
            logger.error(f"Failed to create Stripe payment: {e}")
            return None

    async def _create_kaspi_payment(
        self,
        amount: float,
        currency: str,
        payment_id: int,
        description: str,
        customer_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create Kaspi payment (Kazakhstan)"""
        try:
            # Kaspi API endpoint (this is example, actual endpoint may differ)
            url = "https://api.kaspi.kz/payments/v1/create"

            headers = {
                "Authorization": f"Bearer {settings.KASPI_PAYMENT_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "merchant_id": settings.KASPI_PAYMENT_MERCHANT_ID,
                "amount": float(amount),
                "currency": currency,
                "order_id": str(payment_id),
                "description": description,
                "return_url": f"https://your-domain.com/api/v1/payments/{payment_id}/success",
                "fail_url": f"https://your-domain.com/api/v1/payments/{payment_id}/fail"
            }

            if customer_email:
                data["customer_email"] = customer_email

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data, timeout=10.0)
                response.raise_for_status()

                result = response.json()

                logger.info(f"Kaspi payment created: {result.get('payment_id')}")

                return {
                    "provider": "kaspi",
                    "payment_id": result.get("payment_id"),
                    "payment_url": result.get("payment_url"),
                    "amount": amount,
                    "currency": currency,
                    "status": "pending"
                }

        except Exception as e:
            logger.error(f"Failed to create Kaspi payment: {e}")
            return None

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        provider: str = "stripe"
    ) -> bool:
        """Verify webhook signature"""
        if provider == "stripe":
            return self._verify_stripe_signature(payload, signature)
        elif provider == "kaspi":
            return self._verify_kaspi_signature(payload, signature)
        return False

    def _verify_stripe_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            import stripe
            stripe.api_key = settings.STRIPE_API_KEY

            stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except Exception as e:
            logger.error(f"Stripe signature verification failed: {e}")
            return False

    def _verify_kaspi_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Kaspi webhook signature"""
        try:
            # Calculate expected signature
            secret = settings.KASPI_PAYMENT_API_KEY.encode()
            expected_signature = hashlib.sha256(secret + payload).hexdigest()

            return expected_signature == signature
        except Exception as e:
            logger.error(f"Kaspi signature verification failed: {e}")
            return False

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None
    ) -> bool:
        """Refund a payment"""
        try:
            if settings.STRIPE_API_KEY:
                return await self._refund_stripe_payment(payment_intent_id, amount)
            elif settings.KASPI_PAYMENT_API_KEY:
                return await self._refund_kaspi_payment(payment_intent_id, amount)
            return False
        except Exception as e:
            logger.error(f"Failed to refund payment: {e}")
            return False

    async def _refund_stripe_payment(self, payment_intent_id: str, amount: Optional[float]) -> bool:
        """Refund Stripe payment"""
        try:
            url = "https://api.stripe.com/v1/refunds"

            headers = {
                "Authorization": f"Bearer {settings.STRIPE_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "payment_intent": payment_intent_id
            }

            if amount:
                data["amount"] = int(amount * 100)

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data, timeout=10.0)
                response.raise_for_status()

                logger.info(f"Stripe refund created for payment {payment_intent_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to refund Stripe payment: {e}")
            return False

    async def _refund_kaspi_payment(self, payment_id: str, amount: Optional[float]) -> bool:
        """Refund Kaspi payment"""
        try:
            url = f"https://api.kaspi.kz/payments/v1/{payment_id}/refund"

            headers = {
                "Authorization": f"Bearer {settings.KASPI_PAYMENT_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {}
            if amount:
                data["amount"] = float(amount)

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data, timeout=10.0)
                response.raise_for_status()

                logger.info(f"Kaspi refund created for payment {payment_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to refund Kaspi payment: {e}")
            return False


# Singleton instance
payment_gateway_service = PaymentGatewayService()
