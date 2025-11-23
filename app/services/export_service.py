"""Generic export service for CSV/Excel exports

This service eliminates duplication in reports.py where 5 similar
export functions had almost identical logic.
"""

from typing import List, Dict, Any, Optional, Callable, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Select
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import date
import pandas as pd
import io


async def generic_export_handler(
    db: AsyncSession,
    model: Type,
    columns: List[str],
    entity_name: str,
    format: str,
    to_dict_func: Callable[[List[Any]], List[Dict[str, Any]]],
    filters: Optional[Dict[str, Any]] = None,
    order_by = None
) -> StreamingResponse:
    """
    Generic export handler for CSV and Excel formats

    Args:
        db: Database session
        model: SQLAlchemy model class
        columns: Column headers for export
        entity_name: Name for the Excel sheet
        format: "csv" or "xlsx"
        to_dict_func: Function to convert entities to dict list
        filters: Optional filters to apply (field_name: value)
        order_by: Optional order by field

    Returns:
        StreamingResponse with CSV or Excel file

    Example:
        response = await generic_export_handler(
            db=db,
            model=Payment,
            columns=["ID", "Amount", "Status"],
            entity_name="Payments",
            format="csv",
            to_dict_func=payments_to_export_dict,
            filters={"status": "approved"},
            order_by=Payment.created_at.desc()
        )
    """
    # Build query
    query = select(model)

    # Apply filters
    if filters:
        for field_name, value in filters.items():
            if value is not None:
                field = getattr(model, field_name, None)
                if field is not None:
                    if isinstance(value, dict):
                        # Range filter (e.g., {"gte": date1, "lte": date2})
                        if "gte" in value:
                            query = query.where(field >= value["gte"])
                        if "lte" in value:
                            query = query.where(field <= value["lte"])
                    else:
                        # Exact match
                        query = query.where(field == value)

    # Apply ordering
    if order_by is not None:
        query = query.order_by(order_by)

    # Execute query
    result = await db.execute(query)
    entities = result.scalars().all()

    # Convert to dict
    data = to_dict_func(entities)

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # Generate file
    if format == "csv":
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)

        media_type = "text/csv"
        filename = f"{entity_name.lower().replace(' ', '_')}_{date.today()}.csv"
    else:  # xlsx
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=entity_name, index=False)
        buffer.seek(0)

        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{entity_name.lower().replace(' ', '_')}_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def payments_to_export_dict(payments: List[Any]) -> List[Dict[str, Any]]:
    """Convert payments to export format"""
    return [
        {
            "ID": p.id,
            "Contract Number": p.contract.contract_number if p.contract else "",
            "Tenant": p.contract.tenant.full_name if p.contract and p.contract.tenant else "",
            "Amount": float(p.amount),
            "Due Date": p.due_date.strftime("%Y-%m-%d") if p.due_date else "",
            "Payment Date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else "",
            "Status": p.status.value if hasattr(p.status, 'value') else str(p.status),
            "Payment Method": p.payment_method or "",
        }
        for p in payments
    ]


def tenants_to_export_dict(tenants: List[Any]) -> List[Dict[str, Any]]:
    """Convert tenants to export format"""
    return [
        {
            "ID": t.id,
            "Full Name": t.full_name,
            "Email": t.email or "",
            "Phone": t.phone or "",
            "BIN/IIN": t.bin_iin or "",
            "Active": "Yes" if t.is_active else "No",
            "Created At": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        }
        for t in tenants
    ]


def contracts_to_export_dict(contracts: List[Any]) -> List[Dict[str, Any]]:
    """Convert contracts to export format"""
    return [
        {
            "ID": c.id,
            "Contract Number": c.contract_number,
            "Tenant": c.tenant.full_name if c.tenant else "",
            "Premise": f"{c.premise.building.name if c.premise and c.premise.building else ''} - {c.premise.number if c.premise else ''}",
            "Start Date": c.start_date.strftime("%Y-%m-%d") if c.start_date else "",
            "End Date": c.end_date.strftime("%Y-%m-%d") if c.end_date else "",
            "Rent Amount": float(c.rent_amount),
            "Status": c.status.value if hasattr(c.status, 'value') else str(c.status),
        }
        for c in contracts
    ]


def properties_to_export_dict(properties: List[Any]) -> List[Dict[str, Any]]:
    """Convert properties to export format"""
    return [
        {
            "ID": p.id,
            "Name": p.name,
            "Address": p.address,
            "Type": p.property_type or "",
            "Total Area": float(p.total_area) if p.total_area else 0,
            "Created At": p.created_at.strftime("%Y-%m-%d") if p.created_at else "",
        }
        for p in properties
    ]


def premises_to_export_dict(premises: List[Any]) -> List[Dict[str, Any]]:
    """Convert premises to export format"""
    return [
        {
            "ID": p.id,
            "Building": p.building.name if p.building else "",
            "Number": p.number,
            "Floor": p.floor or "",
            "Area": float(p.area),
            "Rent Price": float(p.rent_price),
            "Status": p.status or "",
            "Is Published": "Yes" if p.is_published else "No",
        }
        for p in premises
    ]
