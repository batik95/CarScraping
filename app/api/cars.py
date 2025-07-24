from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.schemas import CarResponse
from app.services.car_service import CarService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[CarResponse])
async def get_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search_id: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_year: Optional[int] = Query(None, ge=1900),
    max_year: Optional[int] = Query(None, le=2030),
    fuel_type: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    available_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get cars with optional filtering"""
    try:
        car_service = CarService(db)
        cars = car_service.get_cars(
            skip=skip,
            limit=limit,
            search_id=search_id,
            brand=brand,
            model=model,
            min_price=min_price,
            max_price=max_price,
            min_year=min_year,
            max_year=max_year,
            fuel_type=fuel_type,
            province=province,
            available_only=available_only
        )
        return cars
    except Exception as e:
        logger.error(f"Error getting cars: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cars")

@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: int, db: Session = Depends(get_db)):
    """Get a specific car by ID"""
    try:
        car_service = CarService(db)
        car = car_service.get_car(car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return car
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting car {car_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve car")

@router.get("/search/{search_id}", response_model=List[CarResponse])
async def get_cars_by_search(
    search_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    available_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get all cars for a specific search"""
    try:
        car_service = CarService(db)
        cars = car_service.get_cars_by_search(
            search_id=search_id,
            skip=skip,
            limit=limit,
            available_only=available_only
        )
        return cars
    except Exception as e:
        logger.error(f"Error getting cars for search {search_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cars for search")

@router.get("/brands/")
async def get_brands(db: Session = Depends(get_db)):
    """Get all available car brands"""
    try:
        car_service = CarService(db)
        brands = car_service.get_brands()
        return {"brands": brands}
    except Exception as e:
        logger.error(f"Error getting brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve brands")

@router.get("/models/{brand}")
async def get_models(brand: str, db: Session = Depends(get_db)):
    """Get all models for a specific brand"""
    try:
        car_service = CarService(db)
        models = car_service.get_models(brand)
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting models for brand {brand}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve models")

@router.get("/filters/")
async def get_filter_options(db: Session = Depends(get_db)):
    """Get all available filter options"""
    try:
        car_service = CarService(db)
        filters = car_service.get_filter_options()
        return filters
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve filter options")