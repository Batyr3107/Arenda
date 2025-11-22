"""
Database initialization script
Creates the first super admin user
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.db.session import Base


async def init_database():
    """Initialize database and create first super admin"""
    print("🔧 Initializing database...")

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created")

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if any super admin exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.role == UserRole.SUPER_ADMIN)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"⚠️  Super admin already exists: {existing_admin.email}")
            response = input("Do you want to create another super admin? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return

        # Get admin credentials
        print("\n👤 Create Super Admin User")
        print("-" * 40)

        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required")
            return

        # Check if email exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"❌ User with email {email} already exists")
            return

        full_name = input("Full Name: ").strip()
        if not full_name:
            print("❌ Full name is required")
            return

        phone = input("Phone (optional): ").strip() or None

        # Password
        while True:
            password = input("Password (min 8 characters): ").strip()
            if len(password) < 8:
                print("❌ Password must be at least 8 characters")
                continue

            password_confirm = input("Confirm Password: ").strip()
            if password != password_confirm:
                print("❌ Passwords do not match")
                continue

            break

        # Create super admin
        hashed_password = get_password_hash(password)
        admin = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role=UserRole.SUPER_ADMIN,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("\n✅ Super admin created successfully!")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Name: {admin.full_name}")
        print(f"   Role: {admin.role}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("   ARENDA - Database Initialization")
    print("=" * 50)
    print()

    try:
        asyncio.run(init_database())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
