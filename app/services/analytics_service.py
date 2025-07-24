from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from app.models.models import Car, PriceHistory
from app.models.schemas import (
    AnalyticsResponse, PriceRange, MileageStats, 
    GeographicDistribution, PriceTrend
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_analytics(
        self,
        search_id: Optional[int] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        fuel_type: Optional[str] = None,
        province: Optional[str] = None,
        days_back: int = 30
    ) -> AnalyticsResponse:
        """Get comprehensive analytics data"""
        
        # Build base query
        query = self._build_query(
            search_id, brand, model, min_price, max_price,
            min_year, max_year, fuel_type, province
        )
        
        # Get basic price statistics
        price_stats = self._get_price_statistics(query)
        
        # Get mileage-based statistics
        mileage_stats = self._get_mileage_statistics(query)
        
        # Get geographic distribution
        geographic_distribution = self._get_geographic_distribution(query)
        
        # Get price trends
        price_trends = self._get_price_trends(query, days_back)
        
        # Get average age
        avg_age = self._get_average_age(query)
        
        # Get distributions
        fuel_distribution = self._get_fuel_type_distribution(query)
        transmission_distribution = self._get_transmission_distribution(query)
        
        # Total count
        total_cars = query.count()
        
        return AnalyticsResponse(
            total_cars=total_cars,
            price_stats=price_stats,
            mileage_stats=mileage_stats,
            geographic_distribution=geographic_distribution,
            price_trends=price_trends,
            avg_age_years=avg_age,
            fuel_type_distribution=fuel_distribution,
            transmission_distribution=transmission_distribution
        )

    def _build_query(self, search_id, brand, model, min_price, max_price, 
                    min_year, max_year, fuel_type, province):
        """Build filtered query"""
        query = self.db.query(Car).filter(Car.is_available == True)
        
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
        
        return query

    def _get_price_statistics(self, query) -> PriceRange:
        """Get price statistics"""
        stats = query.with_entities(
            func.min(Car.price).label('min_price'),
            func.max(Car.price).label('max_price'),
            func.avg(Car.price).label('avg_price'),
            func.count(Car.id).label('count')
        ).first()
        
        # Get median price
        total_count = stats.count
        if total_count > 0:
            median_query = query.order_by(Car.price).offset(total_count // 2).limit(1)
            median_result = median_query.first()
            median_price = median_result.price if median_result else 0
        else:
            median_price = 0
        
        return PriceRange(
            min_price=stats.min_price or 0,
            max_price=stats.max_price or 0,
            avg_price=stats.avg_price or 0,
            median_price=median_price,
            count=stats.count
        )

    def _get_mileage_statistics(self, query) -> MileageStats:
        """Get price statistics by mileage ranges"""
        
        # 0-50k km
        range_0_50k = query.filter(Car.mileage <= 50000)
        stats_0_50k = self._get_price_statistics(range_0_50k)
        
        # 50-100k km
        range_50_100k = query.filter(and_(Car.mileage > 50000, Car.mileage <= 100000))
        stats_50_100k = self._get_price_statistics(range_50_100k)
        
        # 100k+ km
        range_100k_plus = query.filter(Car.mileage > 100000)
        stats_100k_plus = self._get_price_statistics(range_100k_plus)
        
        return MileageStats(
            range_0_50k=stats_0_50k,
            range_50_100k=stats_50_100k,
            range_100k_plus=stats_100k_plus
        )

    def _get_geographic_distribution(self, query) -> List[GeographicDistribution]:
        """Get geographic distribution"""
        geo_stats = query.with_entities(
            Car.province,
            Car.region,
            func.count(Car.id).label('count'),
            func.avg(Car.price).label('avg_price')
        ).filter(
            Car.province.isnot(None)
        ).group_by(Car.province, Car.region).order_by(desc('count')).limit(20).all()
        
        return [
            GeographicDistribution(
                province=stat.province or "Unknown",
                region=stat.region or "Unknown",
                count=stat.count,
                avg_price=stat.avg_price or 0
            )
            for stat in geo_stats
        ]

    def _get_price_trends(self, query, days_back: int) -> List[PriceTrend]:
        """Get price trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get car IDs from main query
        car_ids = [car.id for car in query.all()]
        
        if not car_ids:
            return []
        
        # Query price history
        trends = self.db.query(
            func.date(PriceHistory.recorded_at).label('date'),
            func.avg(PriceHistory.price).label('avg_price'),
            func.count(PriceHistory.id).label('count')
        ).filter(
            PriceHistory.car_id.in_(car_ids),
            PriceHistory.recorded_at >= cutoff_date
        ).group_by(
            func.date(PriceHistory.recorded_at)
        ).order_by('date').all()
        
        return [
            PriceTrend(
                date=trend.date,
                avg_price=trend.avg_price or 0,
                count=trend.count
            )
            for trend in trends
        ]

    def _get_average_age(self, query) -> float:
        """Get average age of cars in years"""
        current_year = datetime.now().year
        avg_year = query.with_entities(
            func.avg(Car.year).label('avg_year')
        ).filter(Car.year.isnot(None)).first()
        
        if avg_year and avg_year.avg_year:
            return current_year - avg_year.avg_year
        return 0

    def _get_fuel_type_distribution(self, query) -> Dict[str, int]:
        """Get fuel type distribution"""
        distribution = query.with_entities(
            Car.fuel_type,
            func.count(Car.id).label('count')
        ).filter(
            Car.fuel_type.isnot(None)
        ).group_by(Car.fuel_type).all()
        
        return {fuel.fuel_type: fuel.count for fuel in distribution}

    def _get_transmission_distribution(self, query) -> Dict[str, int]:
        """Get transmission distribution"""
        distribution = query.with_entities(
            Car.transmission,
            func.count(Car.id).label('count')
        ).filter(
            Car.transmission.isnot(None)
        ).group_by(Car.transmission).all()
        
        return {trans.transmission: trans.count for trans in distribution}

    def get_price_trends(
        self,
        search_id: Optional[int] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        days_back: int = 30
    ) -> List[PriceTrend]:
        """Get price trends for specific filters"""
        query = self._build_query(search_id, brand, model, None, None, None, None, None, None)
        return self._get_price_trends(query, days_back)

    def get_geographic_distribution(
        self,
        search_id: Optional[int] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[GeographicDistribution]:
        """Get geographic distribution for specific filters"""
        query = self._build_query(search_id, brand, model, None, None, None, None, None, None)
        return self._get_geographic_distribution(query)