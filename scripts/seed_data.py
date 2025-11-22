"""
Seed database with test data
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.property import Property, Building, Premise, PropertyType, PremiseType, PremiseStatus
from app.models.tenant import Tenant, TenantType, TenantContact
from app.models.contract import Contract, ContractStatus, PaymentFrequency
from app.db.session import Base


async def seed_database():
    """Seed database with test data"""
    print("🌱 Seeding database with test data...")

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. Create test company
        company = Company(
            name="Test Company",
            legal_name="ТОО Test Company Kazakhstan",
            bin_iin="123456789012",
            address="Almaty, Abay Avenue 150",
            phone="+7 727 123 4567",
            email="info@testcompany.kz",
            bank_name="Kaspi Bank",
            bank_account="KZ123456789012345678",
            director_name="Иванов Иван Иванович"
        )
        session.add(company)
        await session.flush()
        print(f"✅ Created company: {company.name}")

        # 2. Create test users
        admin = User(
            email="admin@testcompany.kz",
            full_name="Admin User",
            phone="+7 701 111 1111",
            role=UserRole.PROPERTY_ADMIN,
            company_id=company.id,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True
        )
        session.add(admin)

        moderator = User(
            email="moderator@testcompany.kz",
            full_name="Moderator User",
            phone="+7 701 222 2222",
            role=UserRole.MODERATOR,
            company_id=company.id,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True
        )
        session.add(moderator)

        sales = User(
            email="sales@testcompany.kz",
            full_name="Sales Manager",
            phone="+7 701 333 3333",
            role=UserRole.SALES_MANAGER,
            company_id=company.id,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True
        )
        session.add(sales)
        await session.flush()
        print(f"✅ Created {3} test users")

        # 3. Create test property
        property1 = Property(
            name="Business Center Alpha",
            property_type=PropertyType.BUSINESS_CENTER,
            address="Almaty, Al-Farabi Avenue 77",
            city="Almaty",
            total_area=5000.0,
            description="Modern business center in the heart of Almaty",
            company_id=company.id,
            amenities=["Parking", "Security", "Elevator", "WiFi"]
        )
        session.add(property1)
        await session.flush()
        print(f"✅ Created property: {property1.name}")

        # 4. Create building
        building1 = Building(
            property_id=property1.id,
            name="Building A",
            floors=10,
            year_built=2020
        )
        session.add(building1)
        await session.flush()
        print(f"✅ Created building: {building1.name}")

        # 5. Create premises
        premises = []
        for floor in range(1, 6):
            for office in range(1, 5):
                premise = Premise(
                    building_id=building1.id,
                    number=f"{floor}0{office}",
                    floor=floor,
                    area=50.0 + (office * 10),
                    premise_type=PremiseType.OFFICE,
                    status=PremiseStatus.AVAILABLE,
                    price_per_month=Decimal(150000 + (floor * 10000)),
                    is_published=True
                )
                premises.append(premise)
                session.add(premise)

        await session.flush()
        print(f"✅ Created {len(premises)} premises")

        # 6. Create test tenants
        tenant1 = Tenant(
            name="IT Solutions LLP",
            tenant_type=TenantType.LEGAL_ENTITY,
            bin_iin="987654321098",
            email="contact@itsolutions.kz",
            phone="+7 701 444 4444",
            address="Almaty",
            company_id=company.id,
            is_active=True
        )
        session.add(tenant1)

        tenant2 = Tenant(
            name="Consulting Group",
            tenant_type=TenantType.LEGAL_ENTITY,
            bin_iin="555666777888",
            email="info@consulting.kz",
            phone="+7 701 555 5555",
            address="Almaty",
            company_id=company.id,
            is_active=True
        )
        session.add(tenant2)
        await session.flush()
        print(f"✅ Created {2} test tenants")

        # 7. Add contacts for tenants
        contact1 = TenantContact(
            tenant_id=tenant1.id,
            full_name="Петров Петр Петрович",
            position="Director",
            phone="+7 701 444 4444",
            email="p.petrov@itsolutions.kz",
            is_primary=True
        )
        session.add(contact1)

        contact2 = TenantContact(
            tenant_id=tenant2.id,
            full_name="Сидоров Сидор Сидорович",
            position="CEO",
            phone="+7 701 555 5555",
            email="s.sidorov@consulting.kz",
            is_primary=True
        )
        session.add(contact2)
        await session.flush()
        print(f"✅ Created {2} tenant contacts")

        # 8. Create active contracts
        today = date.today()
        contract1 = Contract(
            tenant_id=tenant1.id,
            premise_id=premises[0].id,
            contract_number=f"CNT-2024-001",
            start_date=today,
            end_date=today + timedelta(days=365),
            monthly_rent=Decimal(200000),
            deposit_amount=Decimal(400000),
            payment_frequency=PaymentFrequency.MONTHLY,
            payment_day=5,
            late_fee_percentage=Decimal(0.5),
            status=ContractStatus.ACTIVE
        )
        session.add(contract1)
        premises[0].status = PremiseStatus.OCCUPIED

        contract2 = Contract(
            tenant_id=tenant2.id,
            premise_id=premises[1].id,
            contract_number=f"CNT-2024-002",
            start_date=today,
            end_date=today + timedelta(days=365),
            monthly_rent=Decimal(250000),
            deposit_amount=Decimal(500000),
            payment_frequency=PaymentFrequency.MONTHLY,
            payment_day=10,
            late_fee_percentage=Decimal(0.5),
            status=ContractStatus.ACTIVE
        )
        session.add(contract2)
        premises[1].status = PremiseStatus.OCCUPIED

        await session.flush()
        print(f"✅ Created {2} active contracts")

        # Commit all changes
        await session.commit()

        print("\n" + "=" * 50)
        print("✅ Database seeded successfully!")
        print("=" * 50)
        print(f"\n📊 Test Data Summary:")
        print(f"   - Company: {company.name}")
        print(f"   - Users: 3 (admin, moderator, sales)")
        print(f"   - Properties: 1")
        print(f"   - Buildings: 1")
        print(f"   - Premises: {len(premises)}")
        print(f"   - Tenants: 2")
        print(f"   - Active Contracts: 2")
        print(f"\n🔑 Test Login Credentials:")
        print(f"   Admin:     admin@testcompany.kz / password123")
        print(f"   Moderator: moderator@testcompany.kz / password123")
        print(f"   Sales:     sales@testcompany.kz / password123")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("   ARENDA - Database Seeding")
    print("=" * 50)
    print()

    try:
        asyncio.run(seed_database())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
