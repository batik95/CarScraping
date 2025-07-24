from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Search(Base):
    """Saved search configurations"""
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Filter criteria
    brand = Column(String(100))
    model = Column(String(100))
    variant = Column(String(100))
    fuel_type = Column(String(50))
    transmission = Column(String(50))
    body_type = Column(String(50))
    color = Column(String(50))
    province = Column(String(100))
    
    # Range filters
    year_min = Column(Integer)
    year_max = Column(Integer)
    mileage_min = Column(Integer)
    mileage_max = Column(Integer)
    price_min = Column(Float)
    price_max = Column(Float)
    power_min = Column(Integer)
    power_max = Column(Integer)
    
    # Additional filters as JSON
    additional_filters = Column(JSON)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cars = relationship("Car", back_populates="search")

class Car(Base):
    """Car listings data"""
    __tablename__ = "cars"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True)  # AutoScout24 ID
    url = Column(Text, nullable=False)
    
    # Basic info
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    variant = Column(String(200))
    year = Column(Integer, index=True)
    mileage = Column(Integer, index=True)
    price = Column(Float, nullable=False, index=True)
    
    # Technical specs
    fuel_type = Column(String(50), index=True)
    power_cv = Column(Integer)
    power_kw = Column(Integer)
    transmission = Column(String(50))
    body_type = Column(String(50))
    color = Column(String(50))
    doors = Column(Integer)
    seats = Column(Integer)
    emission_class = Column(String(20))
    
    # Location & seller
    province = Column(String(100), index=True)
    region = Column(String(100), index=True)
    seller_type = Column(String(50))  # Private/Dealer
    
    # Metadata
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    is_available = Column(Boolean, default=True)
    
    # Raw data
    raw_data = Column(JSON)  # Store original scraped data
    
    # Foreign keys
    search_id = Column(Integer, ForeignKey("searches.id"))
    
    # Relationships
    search = relationship("Search", back_populates="cars")
    price_history = relationship("PriceHistory", back_populates="car")

class PriceHistory(Base):
    """Price tracking history"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    price = Column(Float, nullable=False)
    mileage = Column(Integer)  # Mileage at time of price record
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    car = relationship("Car", back_populates="price_history")

class ScrapingLog(Base):
    """Scraping operation logs"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"))
    
    # Operation details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False)  # success, failed, partial
    
    # Results
    cars_found = Column(Integer, default=0)
    cars_new = Column(Integer, default=0)
    cars_updated = Column(Integer, default=0)
    
    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Performance metrics
    duration_seconds = Column(Float)
    pages_scraped = Column(Integer)
    requests_made = Column(Integer)