import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from sqlalchemy.orm import Session
from urllib.parse import urlencode, urlparse, parse_qs
import time
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.models.models import Car, Search, ScrapingLog, PriceHistory
from app.core.config import settings

logger = logging.getLogger(__name__)

class AutoScout24Scraper:
    def __init__(self, db: Session):
        self.db = db
        self.ua = UserAgent()
        self.base_url = settings.autoscout24_base_url
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Setup session with headers and settings"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def _build_search_url(self, search: Search) -> str:
        """Build AutoScout24 search URL from search parameters"""
        params = {}
        
        # Basic filters
        if search.brand:
            params['make'] = search.brand
        if search.model:
            params['model'] = search.model
        if search.fuel_type:
            params['fuel'] = search.fuel_type
        if search.transmission:
            params['transmission'] = search.transmission
        if search.body_type:
            params['body'] = search.body_type
        if search.color:
            params['color'] = search.color
        
        # Range filters
        if search.year_min:
            params['yearfrom'] = search.year_min
        if search.year_max:
            params['yearto'] = search.year_max
        if search.mileage_min:
            params['kmfrom'] = search.mileage_min
        if search.mileage_max:
            params['kmto'] = search.mileage_max
        if search.price_min:
            params['pricefrom'] = int(search.price_min)
        if search.price_max:
            params['priceto'] = int(search.price_max)
        if search.power_min:
            params['powerfrom'] = search.power_min
        if search.power_max:
            params['powerto'] = search.power_max
        
        # Location
        if search.province:
            params['region'] = search.province
        
        # Sort by newest first
        params['sort'] = 'age'
        params['desc'] = '1'
        
        url = f"{self.base_url}/risultati?" + urlencode(params)
        logger.info(f"Built search URL: {url}")
        return url

    async def scrape_search(self, search: Search) -> Dict[str, Any]:
        """Scrape all results for a given search"""
        log_entry = ScrapingLog(
            search_id=search.id,
            started_at=datetime.now(),
            status='running'
        )
        self.db.add(log_entry)
        self.db.commit()
        
        try:
            search_url = self._build_search_url(search)
            
            cars_found = 0
            cars_new = 0
            cars_updated = 0
            pages_scraped = 0
            requests_made = 0
            
            # Start scraping from first page
            page = 1
            has_more_pages = True
            
            while has_more_pages and page <= 50:  # Limit to 50 pages
                page_url = f"{search_url}&page={page}"
                logger.info(f"Scraping page {page}: {page_url}")
                
                try:
                    response = self._make_request(page_url)
                    requests_made += 1
                    
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch page {page}: {response.status_code}")
                        break
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract car listings from page
                    car_listings = self._extract_car_listings(soup)
                    
                    if not car_listings:
                        logger.info(f"No car listings found on page {page}, stopping")
                        has_more_pages = False
                        break
                    
                    for listing_data in car_listings:
                        try:
                            car_result = self._process_car_listing(listing_data, search.id)
                            if car_result['is_new']:
                                cars_new += 1
                            else:
                                cars_updated += 1
                            cars_found += 1
                        except Exception as e:
                            logger.error(f"Error processing car listing: {e}")
                            continue
                    
                    pages_scraped += 1
                    
                    # Check if there's a next page
                    has_more_pages = self._has_next_page(soup)
                    
                    # Delay between requests
                    time.sleep(settings.request_delay)
                    page += 1
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    break
            
            # Update log entry
            log_entry.completed_at = datetime.now()
            log_entry.status = 'success'
            log_entry.cars_found = cars_found
            log_entry.cars_new = cars_new
            log_entry.cars_updated = cars_updated
            log_entry.pages_scraped = pages_scraped
            log_entry.requests_made = requests_made
            log_entry.duration_seconds = (log_entry.completed_at - log_entry.started_at).total_seconds()
            
            self.db.commit()
            
            result = {
                'status': 'success',
                'cars_found': cars_found,
                'cars_new': cars_new,
                'cars_updated': cars_updated,
                'pages_scraped': pages_scraped,
                'requests_made': requests_made,
                'duration_seconds': log_entry.duration_seconds
            }
            
            logger.info(f"Scraping completed for search {search.name}: {result}")
            return result
            
        except Exception as e:
            # Update log entry with error
            log_entry.completed_at = datetime.now()
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.duration_seconds = (log_entry.completed_at - log_entry.started_at).total_seconds()
            
            self.db.commit()
            
            logger.error(f"Scraping failed for search {search.name}: {e}")
            raise

    def _make_request(self, url: str, retries: int = 3) -> requests.Response:
        """Make HTTP request with retries"""
        for attempt in range(retries):
            try:
                # Rotate User-Agent for each request
                self.session.headers['User-Agent'] = self.ua.random
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 2)
        
        raise Exception(f"Failed to fetch {url} after {retries} attempts")

    def _extract_car_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract car listings from page HTML"""
        listings = []
        
        # AutoScout24 uses various selectors, try multiple approaches
        car_containers = soup.find_all('div', {'data-item-name': 'result-item'}) or \
                        soup.find_all('article', class_=re.compile(r'.*listing.*')) or \
                        soup.find_all('div', class_=re.compile(r'.*result.*item.*'))
        
        if not car_containers:
            # Fallback: look for any div with car-related data attributes
            car_containers = soup.find_all('div', attrs={'data-id': True}) or \
                           soup.find_all('a', href=re.compile(r'/auto/'))
        
        logger.info(f"Found {len(car_containers)} potential car containers")
        
        for container in car_containers:
            try:
                listing_data = self._extract_listing_data(container)
                if listing_data and listing_data.get('external_id'):
                    listings.append(listing_data)
            except Exception as e:
                logger.warning(f"Error extracting listing data: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(listings)} car listings")
        return listings

    def _extract_listing_data(self, container) -> Optional[Dict[str, Any]]:
        """Extract data from a single car listing container"""
        data = {}
        
        # Extract external ID from various possible locations
        external_id = container.get('data-id') or \
                     container.get('data-item-id') or \
                     container.get('id')
        
        if not external_id:
            # Try to extract from URL
            link = container.find('a', href=re.compile(r'/auto/'))
            if link:
                href = link.get('href', '')
                id_match = re.search(r'/auto/[^/]+/([^/]+)', href)
                if id_match:
                    external_id = id_match.group(1)
        
        if not external_id:
            return None
        
        data['external_id'] = external_id
        
        # Extract URL
        link = container.find('a', href=re.compile(r'/auto/'))
        if link:
            href = link.get('href', '')
            if href.startswith('/'):
                data['url'] = self.base_url + href
            else:
                data['url'] = href
        else:
            data['url'] = f"{self.base_url}/auto/{external_id}"
        
        # Extract basic information using various selectors
        data.update(self._extract_car_details(container))
        
        return data

    def _extract_car_details(self, container) -> Dict[str, Any]:
        """Extract car details from container using multiple selector strategies"""
        details = {}
        
        # Try to extract title which usually contains brand and model
        title_selectors = [
            'h2', 'h3', '.title', '.listing-title', 
            '[data-testid="ad-title"]', '.cldt-summary-title'
        ]
        
        title_text = ""
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                break
        
        if title_text:
            # Parse brand and model from title
            brand_model = self._parse_brand_model(title_text)
            details.update(brand_model)
            details['variant'] = title_text
        
        # Extract price
        price_selectors = [
            '.price', '.listing-price', '[data-testid="price"]',
            '.cldt-price', '.price-block'
        ]
        
        for selector in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
                if price:
                    details['price'] = price
                    break
        
        # Extract specifications (year, mileage, fuel, etc.)
        spec_text = container.get_text()
        details.update(self._parse_specifications(spec_text))
        
        return details

    def _parse_brand_model(self, title: str) -> Dict[str, str]:
        """Parse brand and model from title"""
        # Common Italian car brands
        brands = [
            'ALFA ROMEO', 'AUDI', 'BMW', 'FIAT', 'FORD', 'MERCEDES', 'MERCEDES-BENZ',
            'NISSAN', 'OPEL', 'PEUGEOT', 'RENAULT', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO',
            'CITROEN', 'HYUNDAI', 'KIA', 'MAZDA', 'MITSUBISHI', 'SEAT', 'SKODA',
            'SUZUKI', 'HONDA', 'JEEP', 'LAND ROVER', 'JAGUAR', 'MINI', 'SMART',
            'LANCIA', 'DACIA', 'TESLA'
        ]
        
        title_upper = title.upper()
        
        for brand in brands:
            if brand in title_upper:
                # Extract model (everything after brand)
                brand_index = title_upper.find(brand)
                model_part = title[brand_index + len(brand):].strip()
                model = model_part.split()[0] if model_part else ""
                
                return {
                    'brand': brand.title(),
                    'model': model
                }
        
        # Fallback: use first word as brand, second as model
        words = title.split()
        return {
            'brand': words[0] if words else "",
            'model': words[1] if len(words) > 1 else ""
        }

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        # Remove currency symbols and spaces
        price_clean = re.sub(r'[€$£\s]', '', price_text)
        # Extract numbers
        price_match = re.search(r'(\d+(?:\.\d+)*)', price_clean.replace(',', ''))
        
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                pass
        
        return None

    def _parse_specifications(self, text: str) -> Dict[str, Any]:
        """Parse specifications from text"""
        specs = {}
        
        # Year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            specs['year'] = int(year_match.group())
        
        # Mileage
        km_match = re.search(r'(\d+(?:\.\d+)*)\s*(?:km|KM)', text.replace(',', ''))
        if km_match:
            specs['mileage'] = int(float(km_match.group(1)))
        
        # Fuel type
        fuel_types = ['benzina', 'diesel', 'gpl', 'metano', 'elettrica', 'ibrida']
        for fuel in fuel_types:
            if fuel.lower() in text.lower():
                specs['fuel_type'] = fuel.title()
                break
        
        # Power
        cv_match = re.search(r'(\d+)\s*(?:cv|CV|hp|HP)', text)
        if cv_match:
            specs['power_cv'] = int(cv_match.group(1))
        
        kw_match = re.search(r'(\d+)\s*(?:kw|KW)', text)
        if kw_match:
            specs['power_kw'] = int(kw_match.group(1))
        
        # Transmission
        if any(word in text.lower() for word in ['automatico', 'automatic']):
            specs['transmission'] = 'Automatico'
        elif any(word in text.lower() for word in ['manuale', 'manual']):
            specs['transmission'] = 'Manuale'
        
        return specs

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page"""
        next_buttons = soup.find_all('a', {'aria-label': 'Next page'}) or \
                      soup.find_all('a', string=re.compile(r'Successiv|Next|>')) or \
                      soup.select('.pagination .next:not(.disabled)')
        
        return len(next_buttons) > 0

    def _process_car_listing(self, listing_data: Dict[str, Any], search_id: int) -> Dict[str, Any]:
        """Process and save a car listing"""
        external_id = listing_data['external_id']
        
        # Check if car already exists
        existing_car = self.db.query(Car).filter(Car.external_id == external_id).first()
        
        if existing_car:
            # Update existing car
            self._update_car(existing_car, listing_data)
            return {'is_new': False, 'car_id': existing_car.id}
        else:
            # Create new car
            new_car = self._create_car(listing_data, search_id)
            return {'is_new': True, 'car_id': new_car.id}

    def _create_car(self, listing_data: Dict[str, Any], search_id: int) -> Car:
        """Create a new car record"""
        car = Car(
            external_id=listing_data['external_id'],
            url=listing_data.get('url', ''),
            brand=listing_data.get('brand', ''),
            model=listing_data.get('model', ''),
            variant=listing_data.get('variant'),
            year=listing_data.get('year'),
            mileage=listing_data.get('mileage'),
            price=listing_data.get('price', 0),
            fuel_type=listing_data.get('fuel_type'),
            power_cv=listing_data.get('power_cv'),
            power_kw=listing_data.get('power_kw'),
            transmission=listing_data.get('transmission'),
            search_id=search_id,
            raw_data=listing_data
        )
        
        self.db.add(car)
        self.db.commit()
        self.db.refresh(car)
        
        # Create initial price history entry
        price_history = PriceHistory(
            car_id=car.id,
            price=car.price,
            mileage=car.mileage
        )
        self.db.add(price_history)
        self.db.commit()
        
        logger.info(f"Created new car: {car.brand} {car.model} (ID: {car.id})")
        return car

    def _update_car(self, car: Car, listing_data: Dict[str, Any]) -> Car:
        """Update existing car record"""
        old_price = car.price
        new_price = listing_data.get('price', car.price)
        
        # Update car data
        car.url = listing_data.get('url', car.url)
        car.variant = listing_data.get('variant', car.variant)
        car.mileage = listing_data.get('mileage', car.mileage)
        car.price = new_price
        car.last_seen = datetime.now()
        car.raw_data = listing_data
        
        # Add price history entry if price changed
        if old_price != new_price:
            price_history = PriceHistory(
                car_id=car.id,
                price=new_price,
                mileage=car.mileage
            )
            self.db.add(price_history)
        
        self.db.commit()
        
        logger.info(f"Updated car: {car.brand} {car.model} (ID: {car.id})")
        return car