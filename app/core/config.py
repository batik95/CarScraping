from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://carscraping:password@localhost:5432/carscraping"
    
    # Redis (for caching)
    redis_url: str = "redis://localhost:6379"
    
    # Scraping settings
    scraping_enabled: bool = True
    scraping_interval_hours: int = 24
    max_retries: int = 3
    request_delay: float = 1.0
    
    # AutoScout24 settings
    autoscout24_base_url: str = "https://www.autoscout24.it"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()