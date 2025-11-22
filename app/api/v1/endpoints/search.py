from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Dict, Any
from app.db.session import get_db
from app.models.user import User
from app.models.property import Property, Premise
from app.models.tenant import Tenant
from app.models.contract import Contract
from app.models.payment import Payment
from app.api.deps import get_moderator_or_higher

router = APIRouter()


@router.get("/global")
async def global_search(
    q: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_moderator_or_higher)
):
    """
    Global search across all entities
    Searches in: properties, premises, tenants, contracts, payments
    """
    results = {
        "query": q,
        "properties": [],
        "premises": [],
        "tenants": [],
        "contracts": [],
        "payments": []
    }

    # Search properties
    property_result = await db.execute(
        select(Property).where(
            or_(
                Property.name.ilike(f"%{q}%"),
                Property.address.ilike(f"%{q}%"),
                Property.city.ilike(f"%{q}%")
            )
        ).limit(10)
    )
    properties = property_result.scalars().all()
    results["properties"] = [
        {
            "id": p.id,
            "name": p.name,
            "type": p.property_type.value if hasattr(p.property_type, 'value') else p.property_type,
            "address": p.address
        }
        for p in properties
    ]

    # Search premises
    premise_result = await db.execute(
        select(Premise).where(
            or_(
                Premise.number.ilike(f"%{q}%"),
                Premise.description.ilike(f"%{q}%")
            )
        ).limit(10)
    )
    premises = premise_result.scalars().all()
    results["premises"] = [
        {
            "id": p.id,
            "number": p.number,
            "floor": p.floor,
            "area": float(p.area),
            "status": p.status.value if hasattr(p.status, 'value') else p.status
        }
        for p in premises
    ]

    # Search tenants
    tenant_result = await db.execute(
        select(Tenant).where(
            or_(
                Tenant.name.ilike(f"%{q}%"),
                Tenant.bin_iin.ilike(f"%{q}%"),
                Tenant.email.ilike(f"%{q}%"),
                Tenant.phone.ilike(f"%{q}%")
            )
        ).limit(10)
    )
    tenants = tenant_result.scalars().all()
    results["tenants"] = [
        {
            "id": t.id,
            "name": t.name,
            "type": t.tenant_type.value if hasattr(t.tenant_type, 'value') else t.tenant_type,
            "bin_iin": t.bin_iin,
            "email": t.email
        }
        for t in tenants
    ]

    # Search contracts
    contract_result = await db.execute(
        select(Contract).where(
            Contract.contract_number.ilike(f"%{q}%")
        ).limit(10)
    )
    contracts = contract_result.scalars().all()
    results["contracts"] = [
        {
            "id": c.id,
            "contract_number": c.contract_number,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "monthly_rent": float(c.monthly_rent)
        }
        for c in contracts
    ]

    # Search payments
    payment_result = await db.execute(
        select(Payment).where(
            Payment.payment_number.ilike(f"%{q}%")
        ).limit(10)
    )
    payments = payment_result.scalars().all()
    results["payments"] = [
        {
            "id": p.id,
            "payment_number": p.payment_number,
            "amount": float(p.amount),
            "status": p.status.value if hasattr(p.status, 'value') else p.status
        }
        for p in payments
    ]

    # Count total results
    total = (
        len(results["properties"]) +
        len(results["premises"]) +
        len(results["tenants"]) +
        len(results["contracts"]) +
        len(results["payments"])
    )
    results["total_results"] = total

    return results
