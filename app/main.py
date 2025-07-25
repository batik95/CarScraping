from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import engine, Base
from app.api import cars, searches, analytics, charts
from app.services.scheduler import scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting CarScraping application...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CarScraping application...")
    scheduler.shutdown()
    logger.info("Scheduler stopped")

# Create FastAPI app
app = FastAPI(
    title="CarScraping",
    description="Car Tracking Tool for AutoScout24.it",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(cars.router, prefix="/api/cars", tags=["cars"])
app.include_router(searches.router, prefix="/api/searches", tags=["searches"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])

@app.get("/")
async def read_root(request: Request):
    """Dashboard homepage"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status for Unraid monitoring"""
    from app.core.database import engine
    from sqlalchemy import text
    import redis as redis_lib
    
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "mode": "unraid" if settings.is_unraid_mode else "standard",
        "checks": {}
    }
    
    # Database health check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis health check
    try:
        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded" if health_status["status"] == "healthy" else "unhealthy"
    
    # Disk space check (for Unraid)
    if settings.is_unraid_mode:
        import shutil
        try:
            total, used, free = shutil.disk_usage("/data")
            health_status["checks"]["disk_space"] = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2), 
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 1)
            }
        except Exception as e:
            health_status["checks"]["disk_space"] = f"error: {str(e)}"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.web_host, port=settings.web_port)