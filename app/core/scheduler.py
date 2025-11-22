"""
Background task scheduler using APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import date, timedelta
import logging

from app.core.config import settings
from app.services.payment_service import update_overdue_payments, send_payment_reminders
from app.services.contract_service import check_contract_expiry
from app.models.contract import Contract, ContractStatus
from app.models.payment import Payment, PaymentStatus
from app.models.tenant import Tenant
from app.utils.email import send_contract_expiring_notification

logger = logging.getLogger(__name__)

# Create async engine for scheduler
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_overdue_payments_job():
    """
    Daily job to check and update overdue payments
    Runs every day at 00:00
    """
    logger.info("🔍 Running overdue payments check...")

    async with async_session() as db:
        try:
            await update_overdue_payments(db)
            logger.info("✅ Overdue payments check completed")
        except Exception as e:
            logger.error(f"❌ Error checking overdue payments: {e}")


async def send_payment_reminders_job():
    """
    Daily job to send payment reminders
    Sends reminders for payments due in 3 days
    Runs every day at 09:00
    """
    logger.info("📧 Sending payment reminders...")

    async with async_session() as db:
        try:
            await send_payment_reminders(db)
            logger.info("✅ Payment reminders sent")
        except Exception as e:
            logger.error(f"❌ Error sending payment reminders: {e}")


async def check_contract_expiry_job():
    """
    Daily job to check for expiring contracts
    Sends notifications for contracts expiring in 30 days
    Runs every day at 10:00
    """
    logger.info("📋 Checking contract expiry...")

    async with async_session() as db:
        try:
            expiring_contracts = await check_contract_expiry(db)

            for contract in expiring_contracts:
                # Load tenant with relationship
                result = await db.execute(
                    select(Contract).where(Contract.id == contract.id)
                )
                contract_with_relations = result.scalar_one()

                # Get tenant
                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.id == contract_with_relations.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()

                if tenant and tenant.email:
                    try:
                        await send_contract_expiring_notification(
                            email_to=tenant.email,
                            tenant_name=tenant.name,
                            contract_number=contract.contract_number,
                            premise_number="N/A",  # TODO: Get from premise
                            end_date=contract.end_date.strftime("%d.%m.%Y")
                        )
                        logger.info(f"✉️  Sent expiry notification to {tenant.email}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send notification to {tenant.email}: {e}")

            logger.info(f"✅ Checked {len(expiring_contracts)} expiring contracts")
        except Exception as e:
            logger.error(f"❌ Error checking contract expiry: {e}")


async def generate_monthly_payments_job():
    """
    Monthly job to generate payment records
    Runs on the 1st of every month at 01:00
    """
    logger.info("💰 Generating monthly payments...")

    async with async_session() as db:
        try:
            # Get all active contracts
            result = await db.execute(
                select(Contract).where(Contract.status == ContractStatus.ACTIVE)
            )
            active_contracts = result.scalars().all()

            total_generated = 0
            for contract in active_contracts:
                from app.services.contract_service import generate_monthly_payments
                payments = await generate_monthly_payments(db, contract)
                total_generated += len(payments)

            logger.info(f"✅ Generated {total_generated} payments for {len(active_contracts)} contracts")
        except Exception as e:
            logger.error(f"❌ Error generating monthly payments: {e}")


async def cleanup_old_notifications_job():
    """
    Weekly job to cleanup old read notifications
    Runs every Sunday at 02:00
    """
    logger.info("🧹 Cleaning up old notifications...")

    async with async_session() as db:
        try:
            from app.models.notification import Notification
            # Delete notifications older than 90 days that are read
            cutoff_date = date.today() - timedelta(days=90)

            result = await db.execute(
                select(Notification).where(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date
                )
            )
            old_notifications = result.scalars().all()

            for notification in old_notifications:
                await db.delete(notification)

            await db.commit()
            logger.info(f"✅ Deleted {len(old_notifications)} old notifications")
        except Exception as e:
            logger.error(f"❌ Error cleaning up notifications: {e}")


# Initialize scheduler
scheduler = AsyncIOScheduler(timezone="Asia/Almaty")


def start_scheduler():
    """Start the background task scheduler"""
    logger.info("🚀 Starting background task scheduler...")

    # Daily tasks
    scheduler.add_job(
        check_overdue_payments_job,
        CronTrigger(hour=0, minute=0),  # Every day at 00:00
        id="check_overdue_payments",
        name="Check overdue payments",
        replace_existing=True
    )

    scheduler.add_job(
        send_payment_reminders_job,
        CronTrigger(hour=9, minute=0),  # Every day at 09:00
        id="send_payment_reminders",
        name="Send payment reminders",
        replace_existing=True
    )

    scheduler.add_job(
        check_contract_expiry_job,
        CronTrigger(hour=10, minute=0),  # Every day at 10:00
        id="check_contract_expiry",
        name="Check contract expiry",
        replace_existing=True
    )

    # Monthly tasks
    scheduler.add_job(
        generate_monthly_payments_job,
        CronTrigger(day=1, hour=1, minute=0),  # 1st of every month at 01:00
        id="generate_monthly_payments",
        name="Generate monthly payments",
        replace_existing=True
    )

    # Weekly tasks
    scheduler.add_job(
        cleanup_old_notifications_job,
        CronTrigger(day_of_week='sun', hour=2, minute=0),  # Every Sunday at 02:00
        id="cleanup_old_notifications",
        name="Cleanup old notifications",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Background task scheduler started")
    logger.info("📋 Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"   - {job.name} (ID: {job.id})")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    logger.info("⏹️  Shutting down background task scheduler...")
    scheduler.shutdown()
    logger.info("✅ Scheduler shut down")
