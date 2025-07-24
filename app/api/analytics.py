from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.models.schemas import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    search_id: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_year: Optional[int] = Query(None, ge=1900),
    max_year: Optional[int] = Query(None, le=2030),
    fuel_type: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get analytics data with optional filtering"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_analytics(
            search_id=search_id,
            brand=brand,
            model=model,
            min_price=min_price,
            max_price=max_price,
            min_year=min_year,
            max_year=max_year,
            fuel_type=fuel_type,
            province=province,
            days_back=days_back
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@router.get("/price-trends")
async def get_price_trends(
    search_id: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get price trends over time"""
    try:
        analytics_service = AnalyticsService(db)
        trends = analytics_service.get_price_trends(
            search_id=search_id,
            brand=brand,
            model=model,
            days_back=days_back
        )
        return {"trends": trends}
    except Exception as e:
        logger.error(f"Error getting price trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve price trends")

@router.get("/geographic-distribution")
async def get_geographic_distribution(
    search_id: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get geographic distribution of cars"""
    try:
        analytics_service = AnalyticsService(db)
        distribution = analytics_service.get_geographic_distribution(
            search_id=search_id,
            brand=brand,
            model=model
        )
        return {"distribution": distribution}
    except Exception as e:
        logger.error(f"Error getting geographic distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve geographic distribution")