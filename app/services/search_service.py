from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models.models import Search
from app.models.schemas import SearchCreate, SearchUpdate, SearchResponse
from app.scraping.autoscout24_scraper import AutoScout24Scraper

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def get_searches(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[SearchResponse]:
        """Get all searches with pagination"""
        query = self.db.query(Search)
        if active_only:
            query = query.filter(Search.is_active == True)
        
        searches = query.offset(skip).limit(limit).all()
        return [SearchResponse.model_validate(search) for search in searches]

    def get_search(self, search_id: int) -> Optional[SearchResponse]:
        """Get a search by ID"""
        search = self.db.query(Search).filter(Search.id == search_id).first()
        if search:
            return SearchResponse.model_validate(search)
        return None

    def create_search(self, search_data: SearchCreate) -> SearchResponse:
        """Create a new search"""
        search = Search(**search_data.model_dump(exclude_unset=True))
        self.db.add(search)
        self.db.commit()
        self.db.refresh(search)
        
        logger.info(f"Created new search: {search.name} (ID: {search.id})")
        return SearchResponse.model_validate(search)

    def update_search(self, search_id: int, search_data: SearchUpdate) -> Optional[SearchResponse]:
        """Update an existing search"""
        search = self.db.query(Search).filter(Search.id == search_id).first()
        if not search:
            return None

        update_data = search_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(search, field, value)

        self.db.commit()
        self.db.refresh(search)
        
        logger.info(f"Updated search: {search.name} (ID: {search.id})")
        return SearchResponse.model_validate(search)

    def delete_search(self, search_id: int) -> bool:
        """Delete a search"""
        search = self.db.query(Search).filter(Search.id == search_id).first()
        if not search:
            return False

        self.db.delete(search)
        self.db.commit()
        
        logger.info(f"Deleted search: {search.name} (ID: {search.id})")
        return True

    async def run_search_scraping(self, search_id: int) -> dict:
        """Manually trigger scraping for a specific search"""
        search = self.db.query(Search).filter(Search.id == search_id).first()
        if not search:
            raise ValueError(f"Search with ID {search_id} not found")

        scraper = AutoScout24Scraper(self.db)
        result = await scraper.scrape_search(search)
        
        logger.info(f"Manual scraping completed for search {search.name}: {result}")
        return result