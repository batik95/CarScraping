from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

# Search schemas
class SearchCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    province: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_min: Optional[int] = None
    mileage_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    power_min: Optional[int] = None
    power_max: Optional[int] = None
    additional_filters: Optional[Dict[str, Any]] = None

class SearchUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    province: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_min: Optional[int] = None
    mileage_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    power_min: Optional[int] = None
    power_max: Optional[int] = None
    additional_filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    province: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_min: Optional[int] = None
    mileage_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    power_min: Optional[int] = None
    power_max: Optional[int] = None
    additional_filters: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# Car schemas
class CarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    external_id: str
    url: str
    brand: str
    model: str
    variant: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    price: float
    fuel_type: Optional[str] = None
    power_cv: Optional[int] = None
    power_kw: Optional[int] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    doors: Optional[int] = None
    seats: Optional[int] = None
    emission_class: Optional[str] = None
    province: Optional[str] = None
    region: Optional[str] = None
    seller_type: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    is_available: bool

# Analytics schemas
class PriceRange(BaseModel):
    min_price: float
    max_price: float
    avg_price: float
    median_price: float
    count: int

class MileageStats(BaseModel):
    range_0_50k: PriceRange
    range_50_100k: PriceRange
    range_100k_plus: PriceRange

class GeographicDistribution(BaseModel):
    province: str
    region: str
    count: int
    avg_price: float

class PriceTrend(BaseModel):
    date: datetime
    avg_price: float
    count: int

class AnalyticsResponse(BaseModel):
    total_cars: int
    price_stats: PriceRange
    mileage_stats: MileageStats
    geographic_distribution: List[GeographicDistribution]
    price_trends: List[PriceTrend]
    avg_age_years: float
    fuel_type_distribution: Dict[str, int]
    transmission_distribution: Dict[str, int]