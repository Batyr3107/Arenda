from fastapi import APIRouter
from app.api.v1.endpoints import auth, properties, premises, tenants, contracts, payments, leads, catalog

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(premises.router, prefix="/premises", tags=["Premises"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["Public Catalog"])
