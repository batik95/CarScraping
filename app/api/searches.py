from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.models import Search
from app.models.schemas import SearchCreate, SearchUpdate, SearchResponse
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[SearchResponse])
async def get_searches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get all saved searches"""
    try:
        search_service = SearchService(db)
        searches = search_service.get_searches(skip=skip, limit=limit, active_only=active_only)
        return searches
    except Exception as e:
        logger.error(f"Error getting searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve searches")

@router.get("/{search_id}", response_model=SearchResponse)
async def get_search(search_id: int, db: Session = Depends(get_db)):
    """Get a specific search by ID"""
    try:
        search_service = SearchService(db)
        search = search_service.get_search(search_id)
        if not search:
            raise HTTPException(status_code=404, detail="Search not found")
        return search
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search {search_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search")

@router.post("/", response_model=SearchResponse)
async def create_search(search: SearchCreate, db: Session = Depends(get_db)):
    """Create a new search"""
    try:
        search_service = SearchService(db)
        new_search = search_service.create_search(search)
        return new_search
    except Exception as e:
        logger.error(f"Error creating search: {e}")
        raise HTTPException(status_code=500, detail="Failed to create search")

@router.put("/{search_id}", response_model=SearchResponse)
async def update_search(
    search_id: int, 
    search_update: SearchUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing search"""
    try:
        search_service = SearchService(db)
        updated_search = search_service.update_search(search_id, search_update)
        if not updated_search:
            raise HTTPException(status_code=404, detail="Search not found")
        return updated_search
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating search {search_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update search")

@router.delete("/{search_id}")
async def delete_search(search_id: int, db: Session = Depends(get_db)):
    """Delete a search"""
    try:
        search_service = SearchService(db)
        success = search_service.delete_search(search_id)
        if not success:
            raise HTTPException(status_code=404, detail="Search not found")
        return {"message": "Search deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting search {search_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete search")

@router.post("/{search_id}/run")
async def run_search(search_id: int, db: Session = Depends(get_db)):
    """Manually trigger scraping for a specific search"""
    try:
        search_service = SearchService(db)
        result = await search_service.run_search_scraping(search_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running search {search_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run search")