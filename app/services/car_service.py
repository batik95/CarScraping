from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional, Dict
import logging

from app.models.models import Car
from app.models.schemas import CarResponse

logger = logging.getLogger(__name__)

class CarService:
    def __init__(self, db: Session):
        self.db = db

    def get_cars(
        self,
        skip: int = 0,
        limit: int = 100,
        search_id: Optional[int] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        fuel_type: Optional[str] = None,
        province: Optional[str] = None,
        available_only: bool = True
    ) -> List[CarResponse]:
        """Get cars with filtering"""
        query = self.db.query(Car)
        
        if available_only:
            query = query.filter(Car.is_available == True)
        if search_id:
            query = query.filter(Car.search_id == search_id)
        if brand:
            query = query.filter(Car.brand.ilike(f"%{brand}%"))
        if model:
            query = query.filter(Car.model.ilike(f"%{model}%"))
        if min_price:
            query = query.filter(Car.price >= min_price)
        if max_price:
            query = query.filter(Car.price <= max_price)
        if min_year:
            query = query.filter(Car.year >= min_year)
        if max_year:
            query = query.filter(Car.year <= max_year)
        if fuel_type:
            query = query.filter(Car.fuel_type.ilike(f"%{fuel_type}%"))
        if province:
            query = query.filter(Car.province.ilike(f"%{province}%"))
        
        cars = query.order_by(Car.last_seen.desc()).offset(skip).limit(limit).all()
        return [CarResponse.model_validate(car) for car in cars]

    def get_car(self, car_id: int) -> Optional[CarResponse]:
        """Get a car by ID"""
        car = self.db.query(Car).filter(Car.id == car_id).first()
        if car:
            return CarResponse.model_validate(car)
        return None

    def get_cars_by_search(
        self,
        search_id: int,
        skip: int = 0,
        limit: int = 100,
        available_only: bool = True
    ) -> List[CarResponse]:
        """Get all cars for a specific search"""
        query = self.db.query(Car).filter(Car.search_id == search_id)
        
        if available_only:
            query = query.filter(Car.is_available == True)
        
        cars = query.order_by(Car.last_seen.desc()).offset(skip).limit(limit).all()
        return [CarResponse.model_validate(car) for car in cars]

    def get_brands(self) -> List[str]:
        """Get all unique car brands"""
        brands = self.db.query(distinct(Car.brand)).filter(
            Car.brand.isnot(None),
            Car.is_available == True
        ).order_by(Car.brand).all()
        return [brand[0] for brand in brands]

    def get_models(self, brand: str) -> List[str]:
        """Get all models for a specific brand"""
        models = self.db.query(distinct(Car.model)).filter(
            Car.brand.ilike(f"%{brand}%"),
            Car.model.isnot(None),
            Car.is_available == True
        ).order_by(Car.model).all()
        return [model[0] for model in models]

    def get_filter_options(self) -> Dict:
        """Get all available filter options"""
        # Get distinct values for filter dropdowns
        brands = self.get_brands()
        
        fuel_types = self.db.query(distinct(Car.fuel_type)).filter(
            Car.fuel_type.isnot(None),
            Car.is_available == True
        ).order_by(Car.fuel_type).all()
        
        transmissions = self.db.query(distinct(Car.transmission)).filter(
            Car.transmission.isnot(None),
            Car.is_available == True
        ).order_by(Car.transmission).all()
        
        body_types = self.db.query(distinct(Car.body_type)).filter(
            Car.body_type.isnot(None),
            Car.is_available == True
        ).order_by(Car.body_type).all()
        
        colors = self.db.query(distinct(Car.color)).filter(
            Car.color.isnot(None),
            Car.is_available == True
        ).order_by(Car.color).all()
        
        provinces = self.db.query(distinct(Car.province)).filter(
            Car.province.isnot(None),
            Car.is_available == True
        ).order_by(Car.province).all()
        
        # Get min/max values for ranges
        price_range = self.db.query(
            func.min(Car.price).label('min_price'),
            func.max(Car.price).label('max_price')
        ).filter(Car.is_available == True).first()
        
        year_range = self.db.query(
            func.min(Car.year).label('min_year'),
            func.max(Car.year).label('max_year')
        ).filter(Car.year.isnot(None), Car.is_available == True).first()
        
        mileage_range = self.db.query(
            func.min(Car.mileage).label('min_mileage'),
            func.max(Car.mileage).label('max_mileage')
        ).filter(Car.mileage.isnot(None), Car.is_available == True).first()
        
        power_range = self.db.query(
            func.min(Car.power_cv).label('min_power'),
            func.max(Car.power_cv).label('max_power')
        ).filter(Car.power_cv.isnot(None), Car.is_available == True).first()
        
        return {
            "brands": brands,
            "fuel_types": [ft[0] for ft in fuel_types],
            "transmissions": [t[0] for t in transmissions],
            "body_types": [bt[0] for bt in body_types],
            "colors": [c[0] for c in colors],
            "provinces": [p[0] for p in provinces],
            "price_range": {
                "min": price_range.min_price if price_range and price_range.min_price else 0,
                "max": price_range.max_price if price_range and price_range.max_price else 100000
            },
            "year_range": {
                "min": year_range.min_year if year_range and year_range.min_year else 2000,
                "max": year_range.max_year if year_range and year_range.max_year else 2024
            },
            "mileage_range": {
                "min": mileage_range.min_mileage if mileage_range and mileage_range.min_mileage else 0,
                "max": mileage_range.max_mileage if mileage_range and mileage_range.max_mileage else 300000
            },
            "power_range": {
                "min": power_range.min_power if power_range and power_range.min_power else 50,
                "max": power_range.max_power if power_range and power_range.max_power else 1000
            }
        }