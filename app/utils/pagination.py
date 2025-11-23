"""
Pagination utilities for consistent query pagination
Eliminates 18+ repeated pagination patterns across endpoints
"""
from typing import List, TypeVar, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from sqlalchemy.sql import Select
from app.db.session import Base

T = TypeVar('T', bound=Base)


async def paginate_query(
    db: AsyncSession,
    query: Select,
    skip: int = 0,
    limit: int = 20,
    order_by_field: Optional[Any] = None,
    order_desc: bool = True
) -> List[T]:
    """
    Generic pagination helper with ordering

    Args:
        db: Database session
        query: SQLAlchemy select query
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        order_by_field: Field to order by (e.g., Property.created_at)
        order_desc: If True, order descending; if False, ascending

    Returns:
        List of model instances

    Example:
        query = select(Property).where(Property.company_id == company_id)
        properties = await paginate_query(
            db, query,
            skip=skip,
            limit=limit,
            order_by_field=Property.created_at,
            order_desc=True
        )
    """
    # Add ordering if specified
    if order_by_field is not None:
        if order_desc:
            query = query.order_by(desc(order_by_field))
        else:
            query = query.order_by(asc(order_by_field))

    # Add pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    return result.scalars().all()


async def paginate_and_count(
    db: AsyncSession,
    query: Select,
    skip: int = 0,
    limit: int = 20,
    order_by_field: Optional[Any] = None,
    order_desc: bool = True
) -> tuple[List[T], int]:
    """
    Paginate with total count (for pagination metadata)

    Returns:
        Tuple of (items, total_count)

    Example:
        items, total = await paginate_and_count(db, query, skip, limit)
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1,
            "pages": (total + limit - 1) // limit
        }
    """
    from sqlalchemy import func

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated items
    items = await paginate_query(
        db, query, skip, limit, order_by_field, order_desc
    )

    return items, total


class PaginationParams:
    """
    Reusable dependency for pagination parameters

    Example:
        from fastapi import Depends

        @router.get("")
        async def list_items(
            pagination: PaginationParams = Depends(),
            db: AsyncSession = Depends(get_db)
        ):
            items = await paginate_query(
                db, select(Item),
                skip=pagination.skip,
                limit=pagination.limit
            )
            return items
    """

    def __init__(
        self,
        skip: int = 0,
        limit: int = 20
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), 100)  # Enforce max 100


class PaginationResponse:
    """
    Standard pagination response format

    Example:
        items = await paginate_query(db, query, skip, limit)
        return PaginationResponse(
            items=items,
            total=100,
            skip=skip,
            limit=limit
        ).to_dict()
    """

    def __init__(
        self,
        items: List[Any],
        total: int,
        skip: int,
        limit: int
    ):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit

    @property
    def page(self) -> int:
        """Current page number (1-indexed)"""
        return (self.skip // self.limit) + 1

    @property
    def pages(self) -> int:
        """Total number of pages"""
        return (self.total + self.limit - 1) // self.limit

    @property
    def has_next(self) -> bool:
        """Whether there are more items"""
        return self.skip + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        """Whether there are previous items"""
        return self.skip > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }
