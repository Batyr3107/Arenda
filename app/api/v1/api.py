from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, companies, users, properties, premises, tenants, contracts, payments,
    leads, catalog, files, reports, notifications, search, bulk, audit, analytics,
    webhooks, settings, telegram, scheduled_reports, maintenance
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(premises.router, prefix="/premises", tags=["Premises"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads & CRM"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Public Catalog"])
api_router.include_router(files.router, prefix="/files", tags=["File Management"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(bulk.router, prefix="/bulk", tags=["Bulk Operations"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Log"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["Telegram Bot"])
api_router.include_router(scheduled_reports.router, prefix="/scheduled-reports", tags=["Scheduled Reports"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance Requests"])
