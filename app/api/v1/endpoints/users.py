from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.api.deps import get_super_admin, get_admin_or_higher
from app.core.security import get_password_hash
from app.utils.repository import get_entity_or_404, check_unique_field
from app.utils.models import update_model_fields

router = APIRouter()


class PasswordChange(BaseModel):
    new_password: str = Field(..., min_length=8)


class RoleChange(BaseModel):
    role: UserRole


class ActivationChange(BaseModel):
    is_active: bool


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Create new user (Admin or higher)"""
    # Check if user with this email already exists
    await check_unique_field(
        db, User, User.email, user_data.email,
        error_message="User with this email already exists"
    )

    # Only super admins can create super admins
    if user_data.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create super admin users"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.model_dump()
    user_dict.pop('password')
    user = User(**user_dict, hashed_password=hashed_password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Search by name or email"),
    role: UserRole = Query(None, description="Filter by role"),
    is_active: bool = Query(None, description="Filter by active status"),
    company_id: int = Query(None, description="Filter by company"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """List all users with filters (Admin or higher)"""
    query = select(User)

    if search:
        query = query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    if role:
        query = query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if company_id:
        query = query.where(User.company_id == company_id)

    # Property admins can only see users from their company
    if current_user.role == UserRole.PROPERTY_ADMIN:
        query = query.where(User.company_id == current_user.company_id)

    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Get user by ID (Admin or higher)"""
    user = await get_entity_or_404(db, User, user_id, "User")

    # Property admins can only view users from their company
    if current_user.role == UserRole.PROPERTY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Update user (Admin or higher)"""
    user = await get_entity_or_404(db, User, user_id, "User")

    # Property admins can only update users from their company
    if current_user.role == UserRole.PROPERTY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if email is being changed and if it's already taken
    if user_data.email and user_data.email != user.email:
        await check_unique_field(
            db, User, User.email, user_data.email,
            exclude_id=user_id,
            error_message="User with this email already exists"
        )

    # Update fields
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role_data: RoleChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Change user role (Super Admin only)"""
    user = await get_entity_or_404(db, User, user_id, "User")

    user.role = role_data.role
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_deactivate_user(
    user_id: int,
    activation_data: ActivationChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Activate or deactivate user (Admin or higher)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Property admins can only activate/deactivate users from their company
    if current_user.role == UserRole.PROPERTY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Prevent deactivating yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )

    user.is_active = activation_data.is_active
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/password", status_code=status.HTTP_200_OK)
async def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_or_higher)
):
    """Change user password (Admin or higher)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Property admins can only change passwords for users from their company
    if current_user.role == UserRole.PROPERTY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Hash and update password
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Delete user (Super Admin only)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    await db.delete(user)
    await db.commit()
    return None
