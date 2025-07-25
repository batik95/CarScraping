from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Web Server
    web_port: int = 8787
    web_host: str = "0.0.0.0"
    
    # Database - Support both embedded and external
    database_url: str = "postgresql://carscraping:carscraping@localhost:5432/carscraping"
    
    # Redis (for caching)
    redis_url: str = "redis://localhost:6379"
    
    # Scraping settings - Support both hour-based and legacy format
    scraping_enabled: bool = True
    scraping_interval_hours: int = 24
    scraping_interval: Optional[str] = None  # For backward compatibility with "24h" format
    max_retries: int = 3
    request_delay: float = 1.0
    
    # AutoScout24 settings
    autoscout24_base_url: str = "https://www.autoscout24.it"
    
    # Environment
    environment: str = "production"
    debug: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "/logs"
    
    # Unraid specific - User/Group IDs for file permissions
    puid: int = 99
    pgid: int = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Handle legacy scraping interval format (e.g., "24h" -> 24)
        if self.scraping_interval:
            if self.scraping_interval.endswith('h'):
                try:
                    self.scraping_interval_hours = int(self.scraping_interval[:-1])
                except ValueError:
                    pass  # Keep default value
            else:
                try:
                    self.scraping_interval_hours = int(self.scraping_interval)
                except ValueError:
                    pass  # Keep default value
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
    
    @property
    def is_embedded_mode(self) -> bool:
        """Check if running in embedded database mode (Unraid)"""
        return "localhost" in self.database_url or "127.0.0.1" in self.database_url
    
    @property
    def is_unraid_mode(self) -> bool:
        """Check if running in Unraid container mode"""
        return os.path.exists("/config") and os.path.exists("/data")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()