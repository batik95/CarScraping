# CarScraping Development Setup Guide

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for caching)

### Step-by-step Setup

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd CarScraping
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database setup**
   ```bash
   # Create PostgreSQL database
   createdb carscraping
   
   # Set environment variables
   export DATABASE_URL="postgresql://username:password@localhost:5432/carscraping"
   
   # Run migrations
   alembic upgrade head
   ```

3. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Development

### Adding New Endpoints

1. **Create new API router** in `app/api/`
2. **Add business logic** in `app/services/`
3. **Include router** in `app/main.py`

Example:
```python
# app/api/new_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Hello World"}

# app/main.py
from app.api import new_feature
app.include_router(new_feature.router, prefix="/api/new-feature")
```

### Database Changes

1. **Modify models** in `app/models/models.py`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. **Apply migration**:
   ```bash
   alembic upgrade head
   ```

## Frontend Development

### Template Structure
- `app/templates/base.html` - Base template with navigation and common elements
- `app/templates/dashboard.html` - Main dashboard page

### Static Assets
- `app/static/css/style.css` - Custom styles
- `app/static/js/app.js` - JavaScript functionality

### Adding New Pages

1. Create new template in `app/templates/`
2. Add route in `app/main.py` or appropriate API module
3. Update navigation in `base.html` if needed

## Scraping Development

### AutoScout24 Scraper
- Located in `app/scraping/autoscout24_scraper.py`
- Handles robust scraping with retry logic
- Extracts comprehensive car data

### Adding New Sites

1. Create new scraper class in `app/scraping/`
2. Implement similar interface to `AutoScout24Scraper`
3. Add to scheduler in `app/services/scheduler.py`

## Testing

### Running Tests
```bash
# Basic structure tests
python tests/test_basic.py

# API tests (when dependencies are installed)
pytest tests/

# Coverage
pytest --cov=app tests/
```

### Adding Tests
1. Create test files in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures for database testing

## Deployment

### Docker Production Build
```bash
docker build -t carscraping:latest .
docker run -p 8000:8000 carscraping:latest
```

### Environment Variables
```bash
# Production settings
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
ENVIRONMENT=production
DEBUG=false
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=24
```

## Monitoring and Debugging

### Logs
- Application logs: `logs/` directory
- Database queries: Set `DEBUG=true` in environment
- Scraping logs: Stored in `scraping_logs` table

### Health Checks
- Application: `GET /health`
- Database: Check connection in logs
- Redis: Monitor cache hit rates

### Common Issues

1. **Database connection errors**
   - Verify DATABASE_URL
   - Check PostgreSQL is running
   - Ensure database exists

2. **Scraping failures**
   - Check network connectivity
   - Verify AutoScout24 site structure hasn't changed
   - Review rate limiting settings

3. **Frontend issues**
   - Check browser console for JavaScript errors
   - Verify API endpoints are responding
   - Check network requests in DevTools

## Performance Optimization

### Database
- Add indexes for frequently queried fields
- Use database connection pooling
- Implement query optimization

### Caching
- Redis for API responses
- Browser caching for static assets
- Application-level caching for expensive operations

### Scraping
- Implement concurrent scraping with rate limiting
- Use request session pooling
- Cache static data (brands, models)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Ensure all tests pass
5. Submit pull request

### Code Style
- Use Black for Python formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Write docstrings for functions and classes