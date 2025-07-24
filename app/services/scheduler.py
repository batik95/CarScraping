from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import sessionmaker
import logging
import asyncio

from app.core.database import engine
from app.core.config import settings
from app.models.models import Search
from app.scraping.autoscout24_scraper import AutoScout24Scraper

logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = AsyncIOScheduler()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def run_scheduled_scraping():
    """Run scraping for all active searches"""
    if not settings.scraping_enabled:
        logger.info("Scraping is disabled, skipping scheduled run")
        return
    
    logger.info("Starting scheduled scraping for all active searches")
    
    db = SessionLocal()
    try:
        # Get all active searches
        active_searches = db.query(Search).filter(Search.is_active == True).all()
        
        if not active_searches:
            logger.info("No active searches found")
            return
        
        logger.info(f"Found {len(active_searches)} active searches")
        
        # Run scraping for each search
        for search in active_searches:
            try:
                logger.info(f"Starting scraping for search: {search.name}")
                scraper = AutoScout24Scraper(db)
                result = await scraper.scrape_search(search)
                logger.info(f"Completed scraping for search {search.name}: {result}")
                
                # Small delay between searches to be respectful
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error scraping search {search.name}: {e}")
                continue
        
        logger.info("Completed scheduled scraping for all searches")
        
    except Exception as e:
        logger.error(f"Error in scheduled scraping: {e}")
    finally:
        db.close()

def setup_scheduled_jobs():
    """Setup scheduled jobs"""
    if not settings.scraping_enabled:
        logger.info("Scraping is disabled, not scheduling jobs")
        return
    
    # Schedule scraping job
    scheduler.add_job(
        run_scheduled_scraping,
        trigger=IntervalTrigger(hours=settings.scraping_interval_hours),
        id='scheduled_scraping',
        name='Scheduled Car Scraping',
        replace_existing=True,
        max_instances=1
    )
    
    logger.info(f"Scheduled scraping job every {settings.scraping_interval_hours} hours")

# Setup jobs when module is imported
setup_scheduled_jobs()