"""
Audit logging utilities
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from app.models.audit_log import AuditLog, AuditAction


async def log_action(
    db: AsyncSession,
    user_id: Optional[int],
    user_email: Optional[str],
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log an action to the audit log

    Args:
        db: Database session
        user_id: ID of user who performed the action
        user_email: Email of user
        action: Type of action (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity (e.g., "Contract", "Payment")
        entity_id: ID of the entity
        description: Human-readable description
        old_values: Previous state of the entity (for UPDATE/DELETE)
        new_values: New state of the entity (for CREATE/UPDATE)
        ip_address: IP address of the request
        user_agent: User agent string
    """
    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(audit_log)
    await db.flush()


def sanitize_for_audit(obj: Any, exclude_fields: list = None) -> Dict[str, Any]:
    """
    Convert object to dict for audit logging, excluding sensitive fields

    Args:
        obj: Object to convert
        exclude_fields: List of field names to exclude

    Returns:
        Dictionary representation of the object
    """
    if exclude_fields is None:
        exclude_fields = ['password', 'hashed_password', 'token', 'secret_key']

    if hasattr(obj, '__dict__'):
        data = {}
        for key, value in obj.__dict__.items():
            # Skip SQLAlchemy internal fields
            if key.startswith('_'):
                continue

            # Skip excluded fields
            if key in exclude_fields:
                data[key] = '***REDACTED***'
                continue

            # Convert complex types
            if hasattr(value, 'value'):  # Enum
                data[key] = value.value
            elif hasattr(value, 'isoformat'):  # Date/DateTime
                data[key] = value.isoformat()
            elif isinstance(value, (str, int, float, bool, type(None))):
                data[key] = value
            else:
                data[key] = str(value)

        return data
    else:
        return {}


async def log_create(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    entity_type: str,
    entity_id: int,
    entity_data: Any,
    ip_address: str = None,
    user_agent: str = None
):
    """Convenience function for logging CREATE actions"""
    await log_action(
        db=db,
        user_id=user_id,
        user_email=user_email,
        action=AuditAction.CREATE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=f"Created {entity_type} #{entity_id}",
        new_values=sanitize_for_audit(entity_data),
        ip_address=ip_address,
        user_agent=user_agent
    )


async def log_update(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    entity_type: str,
    entity_id: int,
    old_data: Any,
    new_data: Any,
    ip_address: str = None,
    user_agent: str = None
):
    """Convenience function for logging UPDATE actions"""
    await log_action(
        db=db,
        user_id=user_id,
        user_email=user_email,
        action=AuditAction.UPDATE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=f"Updated {entity_type} #{entity_id}",
        old_values=sanitize_for_audit(old_data),
        new_values=sanitize_for_audit(new_data),
        ip_address=ip_address,
        user_agent=user_agent
    )


async def log_delete(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    entity_type: str,
    entity_id: int,
    entity_data: Any,
    ip_address: str = None,
    user_agent: str = None
):
    """Convenience function for logging DELETE actions"""
    await log_action(
        db=db,
        user_id=user_id,
        user_email=user_email,
        action=AuditAction.DELETE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=f"Deleted {entity_type} #{entity_id}",
        old_values=sanitize_for_audit(entity_data),
        ip_address=ip_address,
        user_agent=user_agent
    )
