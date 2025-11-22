from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PropertyType(str, enum.Enum):
    BUSINESS_CENTER = "business_center"
    SHOPPING_CENTER = "shopping_center"
    WAREHOUSE = "warehouse"
    INDUSTRIAL = "industrial"


class PremiseType(str, enum.Enum):
    OFFICE = "office"
    RETAIL = "retail"
    WAREHOUSE = "warehouse"
    PRODUCTION = "production"


class PremiseStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class Property(Base):
    """Объект недвижимости (ТРЦ, бизнес-центр и т.д.)"""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # Basic info
    name = Column(String, nullable=False, index=True)
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Details
    description = Column(Text, nullable=True)
    infrastructure = Column(Text, nullable=True)  # Описание инфраструктуры
    total_area = Column(Float, nullable=True)  # Общая площадь в кв.м
    year_built = Column(Integer, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    has_security = Column(Boolean, default=False)
    has_cctv = Column(Boolean, default=False)
    working_hours = Column(String, nullable=True)

    # Contact
    manager_name = Column(String, nullable=True)
    manager_phone = Column(String, nullable=True)
    manager_email = Column(String, nullable=True)

    # Media
    photos = Column(JSON, nullable=True)  # Array of photo URLs
    videos = Column(JSON, nullable=True)  # Array of video URLs

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="properties")
    buildings = relationship("Building", back_populates="property", cascade="all, delete-orphan")
    assigned_users = relationship("User", back_populates="assigned_property")
    leads = relationship("Lead", back_populates="property")

    def __repr__(self):
        return f"<Property {self.name}>"


class Building(Base):
    """Здание/корпус в составе объекта"""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Basic info
    name = Column(String, nullable=False)  # Номер корпуса или название
    floors_count = Column(Integer, nullable=False)
    total_area = Column(Float, nullable=True)

    # Details
    description = Column(Text, nullable=True)
    has_elevator = Column(Boolean, default=False)
    has_ventilation = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="buildings")
    premises = relationship("Premise", back_populates="building", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Building {self.name}>"


class Premise(Base):
    """Помещение для аренды"""
    __tablename__ = "premises"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)

    # Basic info
    number = Column(String, nullable=False, index=True)
    floor = Column(Integer, nullable=False)
    area = Column(Float, nullable=False)  # Площадь в кв.м
    premise_type = Column(SQLEnum(PremiseType), nullable=False)
    status = Column(SQLEnum(PremiseStatus), nullable=False, default=PremiseStatus.AVAILABLE)

    # Pricing
    price_per_month = Column(Float, nullable=False)  # Цена аренды в месяц
    price_per_sqm = Column(Float, nullable=True)  # Цена за кв.м
    deposit_amount = Column(Float, nullable=True)  # Залог

    # Details
    description = Column(Text, nullable=True)
    has_furniture = Column(Boolean, default=False)
    has_internet = Column(Boolean, default=False)
    has_phone = Column(Boolean, default=False)
    has_conditioning = Column(Boolean, default=False)
    ceiling_height = Column(Float, nullable=True)
    rooms_count = Column(Integer, nullable=True)

    # Media
    photos = Column(JSON, nullable=True)  # Array of photo URLs
    floor_plan = Column(String, nullable=True)  # URL to floor plan
    virtual_tour_url = Column(String, nullable=True)  # URL to 3D tour

    # Public catalog
    is_published = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)  # VIP/Горящее предложение
    views_count = Column(Integer, default=0)

    # SEO
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    seo_keywords = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    building = relationship("Building", back_populates="premises")
    contracts = relationship("Contract", back_populates="premise")
    leads = relationship("Lead", back_populates="premise")

    def __repr__(self):
        return f"<Premise {self.number}>"
