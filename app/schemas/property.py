from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.property import PropertyType, PremiseType, PremiseStatus


# Property schemas
class PropertyBase(BaseModel):
    name: str
    property_type: PropertyType
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    infrastructure: Optional[str] = None
    total_area: Optional[float] = None
    year_built: Optional[int] = None
    parking_spaces: Optional[int] = None
    has_security: bool = False
    has_cctv: bool = False
    working_hours: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[str] = None


class PropertyCreate(PropertyBase):
    company_id: int
    photos: Optional[List[str]] = []
    videos: Optional[List[str]] = []


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[PropertyType] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    infrastructure: Optional[str] = None
    total_area: Optional[float] = None
    year_built: Optional[int] = None
    parking_spaces: Optional[int] = None
    has_security: Optional[bool] = None
    has_cctv: Optional[bool] = None
    working_hours: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[str] = None
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None


class PropertyResponse(PropertyBase):
    id: int
    company_id: int
    photos: Optional[List[str]]
    videos: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Building schemas
class BuildingBase(BaseModel):
    name: str
    floors_count: int
    total_area: Optional[float] = None
    description: Optional[str] = None
    has_elevator: bool = False
    has_ventilation: bool = False


class BuildingCreate(BuildingBase):
    property_id: int


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    floors_count: Optional[int] = None
    total_area: Optional[float] = None
    description: Optional[str] = None
    has_elevator: Optional[bool] = None
    has_ventilation: Optional[bool] = None


class BuildingResponse(BuildingBase):
    id: int
    property_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Premise schemas
class PremiseBase(BaseModel):
    number: str
    floor: int
    area: float
    premise_type: PremiseType
    price_per_month: float
    price_per_sqm: Optional[float] = None
    deposit_amount: Optional[float] = None
    description: Optional[str] = None
    has_furniture: bool = False
    has_internet: bool = False
    has_phone: bool = False
    has_conditioning: bool = False
    ceiling_height: Optional[float] = None
    rooms_count: Optional[int] = None


class PremiseCreate(PremiseBase):
    building_id: int
    status: PremiseStatus = PremiseStatus.AVAILABLE
    photos: Optional[List[str]] = []
    floor_plan: Optional[str] = None
    virtual_tour_url: Optional[str] = None


class PremiseUpdate(BaseModel):
    number: Optional[str] = None
    floor: Optional[int] = None
    area: Optional[float] = None
    premise_type: Optional[PremiseType] = None
    status: Optional[PremiseStatus] = None
    price_per_month: Optional[float] = None
    price_per_sqm: Optional[float] = None
    deposit_amount: Optional[float] = None
    description: Optional[str] = None
    has_furniture: Optional[bool] = None
    has_internet: Optional[bool] = None
    has_phone: Optional[bool] = None
    has_conditioning: Optional[bool] = None
    ceiling_height: Optional[float] = None
    rooms_count: Optional[int] = None
    photos: Optional[List[str]] = None
    floor_plan: Optional[str] = None
    virtual_tour_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None


class PremiseResponse(PremiseBase):
    id: int
    building_id: int
    status: PremiseStatus
    photos: Optional[List[str]]
    floor_plan: Optional[str]
    virtual_tour_url: Optional[str]
    is_published: bool
    is_featured: bool
    views_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PremiseListResponse(BaseModel):
    """Response for public catalog"""
    id: int
    number: str
    floor: int
    area: float
    premise_type: PremiseType
    price_per_month: float
    price_per_sqm: Optional[float]
    description: Optional[str]
    photos: Optional[List[str]]
    is_featured: bool

    class Config:
        from_attributes = True
