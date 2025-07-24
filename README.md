# CarScraping

Car Tracking Tool per monitorare auto specifiche su AutoScout24.it con dashboard analytics.

## Panoramica

Questo progetto implementa un sistema robusto per il tracking di auto usate con focus su qualità dei dati, robustezza del sistema e performance. Include funzionalità di scraping automatico, analytics avanzate e un'interfaccia web intuitiva.

## Funzionalità Principali

### 🔍 Sistema di Ricerca Avanzato
- **Filtri intelligenti**: Menu a tendina interconnessi che si aggiornano automaticamente
- **Range slider**: Anno, Chilometraggio, Prezzo, Potenza
- **Filtri multipli**: Marca, Modello, Variante, Alimentazione, Cambio, Carrozzeria, Colore, Provincia
- **Salvataggio ricerche**: Configurazioni personalizzabili con nome

### 📊 Dashboard Analytics
- **KPI in tempo reale**: Prezzo medio, min/max, distribuzione geografica
- **Statistiche per chilometraggio**: Analisi per fasce 0-50k, 50-100k, 100k+
- **Trend prezzi**: Grafici storici per tracking nel tempo
- **Distribuzione**: Alimentazione, cambio, regioni

### 🤖 Scraping Automatico
- **Target**: AutoScout24.it con parsing HTML intelligente
- **Robustezza**: Fallback su cached data, retry automatico, rotating User-Agent
- **Scheduling**: Scraping giornaliero configurabile
- **Dati completi**: Estrazione di tutti i campi disponibili

### 🗄️ Gestione Dati
- **Database PostgreSQL**: Storico prezzi, tracking cambiamenti
- **Caching**: Sistema Redis per performance
- **API RESTful**: Endpoints per tutte le operazioni CRUD

## Architettura Tecnica

### Stack Tecnologico
- **Backend**: FastAPI con architettura pulita
- **Database**: PostgreSQL per dati strutturati
- **Frontend**: Jinja2 templates + JavaScript + Bootstrap
- **Scraping**: requests + BeautifulSoup con sistema di cache
- **Scheduling**: APScheduler per automazione
- **Containerizzazione**: Docker per deployment

### Struttura Progetto
```
CarScraping/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models/              # Database models (SQLAlchemy)
│   │   ├── models.py        # Definizione tabelle
│   │   └── schemas.py       # Pydantic schemas
│   ├── api/                 # API routes
│   │   ├── cars.py          # Endpoints auto
│   │   ├── searches.py      # Endpoints ricerche
│   │   └── analytics.py     # Endpoints analytics
│   ├── scraping/            # Moduli scraping
│   │   └── autoscout24_scraper.py
│   ├── services/            # Business logic
│   │   ├── car_service.py
│   │   ├── search_service.py
│   │   ├── analytics_service.py
│   │   └── scheduler.py
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   └── dashboard.html
│   ├── static/              # CSS, JS, assets
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── core/               # Configurazione, database
│       ├── config.py
│       └── database.py
├── tests/                   # Unit tests
├── docker-compose.yml       # Docker setup
├── Dockerfile
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisiti
- Docker e Docker Compose
- Python 3.11+ (per sviluppo locale)

### Setup con Docker (Raccomandato)

1. **Clone del repository**
   ```bash
   git clone <repository-url>
   cd CarScraping
   ```

2. **Configurazione environment**
   ```bash
   cp .env.example .env
   # Modifica .env con le tue configurazioni
   ```

3. **Avvio servizi**
   ```bash
   docker-compose up -d
   ```

4. **Accesso dashboard**
   - Apri http://localhost:8000 nel browser
   - L'applicazione si inizializzerà automaticamente

### Setup per Sviluppo

1. **Ambiente virtuale**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oppure
   venv\Scripts\activate     # Windows
   ```

2. **Installazione dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database**
   ```bash
   # Avvia PostgreSQL con Docker
   docker-compose up -d db redis
   
   # Esegui migrazioni
   alembic upgrade head
   ```

4. **Avvio applicazione**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Utilizzo

### 1. Creazione Ricerca
1. Clicca "Nuova Ricerca" nella navbar
2. Imposta i filtri desiderati (marca, modello, prezzo, etc.)
3. Salva con un nome identificativo

### 2. Monitoraggio Dashboard
- **KPI**: Visualizza statistiche in tempo reale
- **Grafici**: Trend prezzi e distribuzioni
- **Tabelle**: Lista dettagliata auto trovate

### 3. Scraping Automatico
- Configurato per eseguire ogni 24 ore (personalizzabile)
- Scraping manuale disponibile per ogni ricerca
- Log dettagliati delle operazioni

### 4. Analisi Dati
- Filtri interattivi per segmentazione
- Export CSV per analisi esterne
- Tracking storico prezzi

## API Endpoints

### Ricerche
- `GET /api/searches/` - Lista ricerche salvate
- `POST /api/searches/` - Crea nuova ricerca
- `PUT /api/searches/{id}` - Aggiorna ricerca
- `DELETE /api/searches/{id}` - Elimina ricerca
- `POST /api/searches/{id}/run` - Esegui scraping

### Auto
- `GET /api/cars/` - Lista auto con filtri
- `GET /api/cars/{id}` - Dettaglio auto
- `GET /api/cars/brands/` - Lista marche
- `GET /api/cars/models/{brand}` - Modelli per marca

### Analytics
- `GET /api/analytics/` - Statistiche complete
- `GET /api/analytics/price-trends` - Trend prezzi
- `GET /api/analytics/geographic-distribution` - Distribuzione geografica

## Configurazione

### Variabili Environment
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Scraping
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=24
MAX_RETRIES=3
REQUEST_DELAY=1.0

# Applicazione
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Personalizzazioni Scraping
- **Frequenza**: Modifica `SCRAPING_INTERVAL_HOURS`
- **Robustezza**: Configura `MAX_RETRIES` e `REQUEST_DELAY`
- **User-Agent**: Rotation automatica per evitare blocchi

## Deployment su Unraid

### Docker Compose per Unraid
```yaml
version: '3.8'
services:
  carscraping:
    image: carscraping:latest
    container_name: CarScraping
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://carscraping:password@carscraping-db:5432/carscraping
    volumes:
      - /mnt/user/appdata/carscraping/logs:/app/logs
    depends_on:
      - carscraping-db
      - carscraping-redis
    restart: unless-stopped

  carscraping-db:
    image: postgres:15
    container_name: CarScraping-DB
    environment:
      POSTGRES_DB: carscraping
      POSTGRES_USER: carscraping
      POSTGRES_PASSWORD: password
    volumes:
      - /mnt/user/appdata/carscraping/postgres:/var/lib/postgresql/data
    restart: unless-stopped

  carscraping-redis:
    image: redis:7-alpine
    container_name: CarScraping-Redis
    volumes:
      - /mnt/user/appdata/carscraping/redis:/data
    restart: unless-stopped
```

## Monitoring e Logs

### Health Checks
- `GET /health` - Status applicazione
- Logs strutturati in `/app/logs`
- Metriche performance scraping

### Troubleshooting
- **Scraping fallito**: Controlla logs per rate limiting
- **Database errori**: Verifica connessione PostgreSQL
- **Performance**: Monitoring Redis cache hit rate

## Contributi

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi `LICENSE` per dettagli.

## Supporto

Per supporto e domande:
- Apri un issue su GitHub
- Controlla la documentazione API
- Verifica i logs dell'applicazione