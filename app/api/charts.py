"""
CarScraping - Advanced Charts API
Enhanced endpoints for Chart.js v4 integration with real-time analytics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.models.models import Car, Search
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/price-trend")
async def get_price_trend(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y, 2y"),
    group_by: str = Query("day", description="Grouping: day, week, month"),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    min_mileage: Optional[int] = Query(None),
    max_mileage: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get price trend data over time with multiple mileage segments
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        period_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30), 
            "90d": timedelta(days=90),
            "1y": timedelta(days=365),
            "2y": timedelta(days=730)
        }
        
        if period not in period_map:
            raise HTTPException(status_code=400, detail="Invalid period")
            
        start_date = end_date - period_map[period]
        
        # Build base query with filters
        query = db.query(Car).filter(
            Car.last_seen >= start_date,
            Car.price.isnot(None)
        )
        
        # Apply filters
        if brand:
            query = query.filter(Car.brand == brand)
        if model:
            query = query.filter(Car.model == model)
        if fuel_type:
            query = query.filter(Car.fuel_type == fuel_type)
        if min_price:
            query = query.filter(Car.price >= min_price)
        if max_price:
            query = query.filter(Car.price <= max_price)
        if min_year:
            query = query.filter(Car.year >= min_year)
        if max_year:
            query = query.filter(Car.year <= max_year)
        if min_mileage:
            query = query.filter(Car.mileage >= min_mileage)
        if max_mileage:
            query = query.filter(Car.mileage <= max_mileage)
        
        # Determine grouping SQL
        if group_by == "day":
            date_trunc = "DATE(last_seen)"
        elif group_by == "week":
            date_trunc = "DATE(last_seen, 'weekday 0', '-7 days')"
        else:  # month
            date_trunc = "DATE(last_seen, 'start of month')"
        
        # Overall trend query
        overall_query = query.with_entities(
            func.strftime('%Y-%m-%d', func.date(Car.last_seen)).label('date'),
            func.avg(Car.price).label('avg_price'),
            func.count(Car.id).label('count')
        ).group_by(
            func.strftime('%Y-%m-%d', func.date(Car.last_seen))
        ).order_by('date')
        
        overall_results = overall_query.all()
        
        # Mileage-based trends
        mileage_ranges = [
            (0, 50000, 'low'),
            (50000, 100000, 'medium'), 
            (100000, float('inf'), 'high')
        ]
        
        mileage_data = {}
        
        for min_km, max_km, range_name in mileage_ranges:
            mileage_query = query.filter(
                Car.mileage >= min_km,
                Car.mileage < max_km if max_km != float('inf') else True
            ).with_entities(
                func.strftime('%Y-%m-%d', func.date(Car.last_seen)).label('date'),
                func.avg(Car.price).label('avg_price'),
                func.count(Car.id).label('count')
            ).group_by(
                func.strftime('%Y-%m-%d', func.date(Car.last_seen))
            ).order_by('date')
            
            mileage_results = mileage_query.all()
            mileage_data[range_name] = [
                {"date": r.date, "value": float(r.avg_price), "count": r.count}
                for r in mileage_results
            ]
        
        # Format results
        dates = [r.date for r in overall_results]
        overall_values = [float(r.avg_price) for r in overall_results]
        
        # Calculate statistics
        if overall_values:
            avg_price = sum(overall_values) / len(overall_values)
            change_percentage = 0
            if len(overall_values) > 1:
                first_val = overall_values[0]
                last_val = overall_values[-1]
                if first_val > 0:
                    change_percentage = ((last_val - first_val) / first_val) * 100
            
            # Calculate volatility (standard deviation)
            mean = avg_price
            variance = sum((x - mean) ** 2 for x in overall_values) / len(overall_values)
            volatility = (variance ** 0.5 / mean) * 100 if mean > 0 else 0
        else:
            avg_price = 0
            change_percentage = 0
            volatility = 0
        
        # Generate trend line (simple linear regression)
        trend_line = []
        if len(overall_values) > 1:
            n = len(overall_values)
            x_values = list(range(n))
            x_sum = sum(x_values)
            y_sum = sum(overall_values)
            xy_sum = sum(x * y for x, y in zip(x_values, overall_values))
            x2_sum = sum(x * x for x in x_values)
            
            if n * x2_sum - x_sum * x_sum != 0:
                slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
                intercept = (y_sum - slope * x_sum) / n
                trend_line = [slope * x + intercept for x in x_values]
        
        return {
            "dates": dates,
            "overall": overall_values,
            "by_mileage": {
                "low": [point["value"] for point in mileage_data.get("low", [])],
                "medium": [point["value"] for point in mileage_data.get("medium", [])],
                "high": [point["value"] for point in mileage_data.get("high", [])]
            },
            "trend_line": trend_line,
            "statistics": {
                "average": avg_price,
                "change_percentage": change_percentage,
                "volatility": volatility,
                "total_data_points": len(overall_results)
            },
            "events": []  # Would be populated with significant market events
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating price trend: {str(e)}")


@router.get("/price-mileage-scatter")
async def get_price_mileage_scatter(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db)
):
    """
    Get price vs mileage scatter plot data colored by age groups
    """
    try:
        current_year = datetime.now().year
        
        # Build query
        query = db.query(Car).filter(
            Car.price.isnot(None),
            Car.mileage.isnot(None),
            Car.year.isnot(None)
        )
        
        # Apply filters
        if brand:
            query = query.filter(Car.brand == brand)
        if model:
            query = query.filter(Car.model == model)
        if fuel_type:
            query = query.filter(Car.fuel_type == fuel_type)
        if min_price:
            query = query.filter(Car.price >= min_price)
        if max_price:
            query = query.filter(Car.price <= max_price)
        if min_year:
            query = query.filter(Car.year >= min_year)
        if max_year:
            query = query.filter(Car.year <= max_year)
        
        # Get results with limit
        results = query.limit(limit).all()
        
        # Group by age ranges
        age_groups = {
            "0-5": [],  # 0-5 years
            "5-10": [], # 5-10 years
            "10+": []   # 10+ years
        }
        
        for car in results:
            age = current_year - car.year
            point = {"x": car.mileage, "y": car.price}
            
            if age <= 5:
                age_groups["0-5"].append(point)
            elif age <= 10:
                age_groups["5-10"].append(point)
            else:
                age_groups["10+"].append(point)
        
        # Calculate correlation coefficient
        all_points = [{"x": car.mileage, "y": car.price} for car in results]
        correlation = calculate_correlation(all_points) if len(all_points) > 1 else 0
        
        return {
            "datasets": [
                {
                    "label": "0-5 anni",
                    "data": age_groups["0-5"],
                    "pointCount": len(age_groups["0-5"])
                },
                {
                    "label": "5-10 anni", 
                    "data": age_groups["5-10"],
                    "pointCount": len(age_groups["5-10"])
                },
                {
                    "label": "10+ anni",
                    "data": age_groups["10+"],
                    "pointCount": len(age_groups["10+"])
                }
            ],
            "statistics": {
                "correlation": correlation,
                "total_points": len(all_points),
                "price_range": {
                    "min": min(point["y"] for point in all_points) if all_points else 0,
                    "max": max(point["y"] for point in all_points) if all_points else 0
                },
                "mileage_range": {
                    "min": min(point["x"] for point in all_points) if all_points else 0,
                    "max": max(point["x"] for point in all_points) if all_points else 0
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating scatter plot: {str(e)}")


@router.get("/geographic-distribution")
async def get_geographic_distribution(
    view: str = Query("regions", description="View type: regions or provinces"),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get geographic distribution of cars and prices
    """
    try:
        # Build query
        query = db.query(Car).filter(Car.price.isnot(None))
        
        # Apply filters
        if brand:
            query = query.filter(Car.brand == brand)
        if model:
            query = query.filter(Car.model == model)
        if fuel_type:
            query = query.filter(Car.fuel_type == fuel_type)
        if min_price:
            query = query.filter(Car.price >= min_price)
        if max_price:
            query = query.filter(Car.price <= max_price)
        
        if view == "regions":
            # Group by regions (simplified mapping)
            region_mapping = get_region_mapping()
            
            # Query grouped by province and map to regions
            province_data = query.with_entities(
                Car.province,
                func.avg(Car.price).label('avg_price'),
                func.count(Car.id).label('count')
            ).filter(Car.province.isnot(None)).group_by(Car.province).all()
            
            # Aggregate by regions
            region_data = {}
            for province_result in province_data:
                region = region_mapping.get(province_result.province, "Altro")
                if region not in region_data:
                    region_data[region] = {"total_price": 0, "count": 0}
                region_data[region]["total_price"] += province_result.avg_price * province_result.count
                region_data[region]["count"] += province_result.count
            
            # Calculate averages
            results = []
            for region, data in region_data.items():
                if data["count"] > 0:
                    avg_price = data["total_price"] / data["count"]
                    results.append({
                        "name": region,
                        "value": avg_price,
                        "count": data["count"]
                    })
            
        else:  # provinces
            results_query = query.with_entities(
                Car.province,
                func.avg(Car.price).label('avg_price'),
                func.count(Car.id).label('count')
            ).filter(Car.province.isnot(None)).group_by(Car.province).all()
            
            results = [
                {
                    "name": result.province,
                    "value": float(result.avg_price),
                    "count": result.count
                }
                for result in results_query
            ]
        
        # Sort by count and take top entries
        results.sort(key=lambda x: x["count"], reverse=True)
        top_results = results[:20]  # Top 20 regions/provinces
        
        return {
            "data": top_results,
            "labels": [item["name"] for item in top_results],
            "values": [item["value"] for item in top_results],
            "counts": [item["count"] for item in top_results],
            "statistics": {
                "total_locations": len(results),
                "average_price": sum(item["value"] * item["count"] for item in results) / sum(item["count"] for item in results) if results else 0,
                "total_cars": sum(item["count"] for item in results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating geographic data: {str(e)}")


@router.get("/price-histogram")
async def get_price_histogram(
    bins: int = Query(20, ge=5, le=50),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get price distribution histogram
    """
    try:
        # Build query
        query = db.query(Car.price).filter(Car.price.isnot(None))
        
        # Apply filters
        if brand:
            query = query.filter(Car.brand == brand)
        if model:
            query = query.filter(Car.model == model)
        if fuel_type:
            query = query.filter(Car.fuel_type == fuel_type)
        if min_year:
            query = query.filter(Car.year >= min_year)
        if max_year:
            query = query.filter(Car.year <= max_year)
        
        # Get all prices
        prices = [float(price[0]) for price in query.all()]
        
        if not prices:
            return {
                "labels": [],
                "data": [],
                "statistics": {"mean": 0, "median": 0, "std": 0, "count": 0}
            }
        
        # Calculate histogram
        min_price = min(prices)
        max_price = max(prices)
        bin_width = (max_price - min_price) / bins
        
        histogram = [0] * bins
        bin_labels = []
        
        for i in range(bins):
            bin_start = min_price + i * bin_width
            bin_end = min_price + (i + 1) * bin_width
            bin_labels.append(f"€{int(bin_start/1000)}k-{int(bin_end/1000)}k")
            
            # Count values in this bin
            count = sum(1 for price in prices if bin_start <= price < bin_end)
            histogram[i] = count
        
        # Handle last bin edge case
        if prices:
            last_bin_count = sum(1 for price in prices if price == max_price)
            if last_bin_count > 0:
                histogram[-1] += last_bin_count
        
        # Calculate statistics
        n = len(prices)
        mean_price = sum(prices) / n
        sorted_prices = sorted(prices)
        median_price = sorted_prices[n // 2] if n % 2 == 1 else (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
        variance = sum((price - mean_price) ** 2 for price in prices) / n
        std_dev = variance ** 0.5
        
        return {
            "labels": bin_labels,
            "data": histogram,
            "statistics": {
                "mean": mean_price,
                "median": median_price,
                "std": std_dev,
                "count": n,
                "min": min_price,
                "max": max_price
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating histogram: {str(e)}")


@router.get("/brand-comparison")
async def get_brand_comparison(
    brands: List[str] = Query(..., description="List of brands to compare"),
    fuel_type: Optional[str] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get radar chart data for brand comparison
    """
    try:
        if len(brands) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 brands allowed")
        
        comparison_data = []
        
        for brand in brands:
            # Build query for this brand
            query = db.query(Car).filter(
                Car.brand == brand,
                Car.price.isnot(None)
            )
            
            # Apply filters
            if fuel_type:
                query = query.filter(Car.fuel_type == fuel_type)
            if min_year:
                query = query.filter(Car.year >= min_year)
            if max_year:
                query = query.filter(Car.year <= max_year)
            
            cars = query.all()
            
            if not cars:
                continue
            
            # Calculate metrics
            prices = [car.price for car in cars if car.price]
            ages = [datetime.now().year - car.year for car in cars if car.year]
            mileages = [car.mileage for car in cars if car.mileage]
            
            metrics = {
                "brand": brand,
                "avg_price": sum(prices) / len(prices) if prices else 0,
                "avg_age": sum(ages) / len(ages) if ages else 0,
                "avg_mileage": sum(mileages) / len(mileages) if mileages else 0,
                "count": len(cars),
                "price_std": (sum((p - sum(prices)/len(prices))**2 for p in prices) / len(prices))**0.5 if len(prices) > 1 else 0
            }
            
            comparison_data.append(metrics)
        
        # Normalize data for radar chart (0-100 scale)
        if comparison_data:
            max_price = max(m["avg_price"] for m in comparison_data)
            max_age = max(m["avg_age"] for m in comparison_data)
            max_mileage = max(m["avg_mileage"] for m in comparison_data)
            max_count = max(m["count"] for m in comparison_data)
            
            for metrics in comparison_data:
                metrics["normalized"] = {
                    "price": (metrics["avg_price"] / max_price * 100) if max_price > 0 else 0,
                    "age": (100 - (metrics["avg_age"] / max_age * 100)) if max_age > 0 else 100,  # Inverted (newer is better)
                    "mileage": (100 - (metrics["avg_mileage"] / max_mileage * 100)) if max_mileage > 0 else 100,  # Inverted (less mileage is better)
                    "availability": (metrics["count"] / max_count * 100) if max_count > 0 else 0
                }
        
        return {
            "brands": [m["brand"] for m in comparison_data],
            "metrics": ["Prezzo", "Età", "Chilometraggio", "Disponibilità"],
            "datasets": [
                {
                    "label": metrics["brand"],
                    "data": [
                        metrics["normalized"]["price"],
                        metrics["normalized"]["age"], 
                        metrics["normalized"]["mileage"],
                        metrics["normalized"]["availability"]
                    ],
                    "raw_data": {
                        "avg_price": metrics["avg_price"],
                        "avg_age": metrics["avg_age"],
                        "avg_mileage": metrics["avg_mileage"],
                        "count": metrics["count"]
                    }
                }
                for metrics in comparison_data
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating brand comparison: {str(e)}")


# Helper functions

def calculate_correlation(points):
    """Calculate Pearson correlation coefficient"""
    if len(points) < 2:
        return 0
    
    n = len(points)
    x_values = [p["x"] for p in points]
    y_values = [p["y"] for p in points]
    
    x_sum = sum(x_values)
    y_sum = sum(y_values)
    xy_sum = sum(x * y for x, y in zip(x_values, y_values))
    x2_sum = sum(x * x for x in x_values)
    y2_sum = sum(y * y for y in y_values)
    
    numerator = n * xy_sum - x_sum * y_sum
    denominator = ((n * x2_sum - x_sum * x_sum) * (n * y2_sum - y_sum * y_sum)) ** 0.5
    
    return numerator / denominator if denominator != 0 else 0


def get_region_mapping():
    """Map Italian provinces to regions"""
    return {
        # Lombardia
        "Milano": "Lombardia", "Bergamo": "Lombardia", "Brescia": "Lombardia",
        "Como": "Lombardia", "Cremona": "Lombardia", "Mantova": "Lombardia",
        "Pavia": "Lombardia", "Sondrio": "Lombardia", "Varese": "Lombardia",
        "Lecco": "Lombardia", "Lodi": "Lombardia", "Monza e Brianza": "Lombardia",
        
        # Lazio
        "Roma": "Lazio", "Frosinone": "Lazio", "Latina": "Lazio",
        "Rieti": "Lazio", "Viterbo": "Lazio",
        
        # Veneto
        "Venezia": "Veneto", "Verona": "Veneto", "Vicenza": "Veneto",
        "Padova": "Veneto", "Treviso": "Veneto", "Rovigo": "Veneto", "Belluno": "Veneto",
        
        # Emilia-Romagna
        "Bologna": "Emilia-Romagna", "Modena": "Emilia-Romagna", "Parma": "Emilia-Romagna",
        "Reggio Emilia": "Emilia-Romagna", "Ferrara": "Emilia-Romagna", "Ravenna": "Emilia-Romagna",
        "Forlì-Cesena": "Emilia-Romagna", "Rimini": "Emilia-Romagna", "Piacenza": "Emilia-Romagna",
        
        # Piemonte
        "Torino": "Piemonte", "Alessandria": "Piemonte", "Asti": "Piemonte",
        "Biella": "Piemonte", "Cuneo": "Piemonte", "Novara": "Piemonte",
        "Verbano-Cusio-Ossola": "Piemonte", "Vercelli": "Piemonte",
        
        # Add more regions as needed...
    }