#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log "CarScraping Unraid Container Starting..."

# Create necessary directories
mkdir -p /data/postgres /data/redis /logs /config

# Set ownership for data directories
chown -R postgres:postgres /data/postgres
chown -R redis:redis /data/redis
chown -R app:app /logs /config

# Initialize PostgreSQL if data directory is empty
if [ ! -f "/data/postgres/PG_VERSION" ]; then
    log "Initializing PostgreSQL database..."
    
    # Initialize PostgreSQL cluster
    gosu postgres initdb -D /data/postgres
    
    # Configure PostgreSQL
    cat > /data/postgres/postgresql.conf << EOF
# PostgreSQL configuration for CarScraping
listen_addresses = '*'
port = 5432
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.utf8'
lc_monetary = 'en_US.utf8'
lc_numeric = 'en_US.utf8'
lc_time = 'en_US.utf8'
default_text_search_config = 'pg_catalog.english'
EOF

    cat > /data/postgres/pg_hba.conf << EOF
# PostgreSQL HBA configuration for CarScraping
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               md5
EOF

    # Start PostgreSQL temporarily to create database and user
    log "Starting PostgreSQL for initial setup..."
    gosu postgres pg_ctl -D /data/postgres -l /logs/postgresql-init.log start
    
    # Wait for PostgreSQL to be ready
    sleep 5
    until gosu postgres pg_isready -q; do
        warn "Waiting for PostgreSQL to be ready..."
        sleep 2
    done
    
    # Create user and database
    log "Creating CarScraping database and user..."
    gosu postgres psql -c "CREATE USER carscraping WITH PASSWORD 'carscraping';"
    gosu postgres psql -c "CREATE DATABASE carscraping OWNER carscraping;"
    gosu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE carscraping TO carscraping;"
    
    # Stop PostgreSQL (supervisor will restart it)
    log "Stopping PostgreSQL initial setup..."
    gosu postgres pg_ctl -D /data/postgres stop
    
    log "PostgreSQL initialization completed!"
else
    log "PostgreSQL data directory exists, skipping initialization"
fi

# Initialize Redis data directory
if [ ! -d "/data/redis" ]; then
    log "Creating Redis data directory..."
    mkdir -p /data/redis
    chown -R redis:redis /data/redis
fi

# Create default environment configuration
if [ ! -f "/config/.env" ]; then
    log "Creating default environment configuration..."
    cat > /config/.env << EOF
# CarScraping Configuration for Unraid
WEB_PORT=8787
WEB_HOST=0.0.0.0
DATABASE_URL=postgresql://carscraping:carscraping@localhost:5432/carscraping
REDIS_URL=redis://localhost:6379
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=${SCRAPING_INTERVAL:-24}
MAX_RETRIES=3
REQUEST_DELAY=1.0
AUTOSCOUT24_BASE_URL=https://www.autoscout24.it
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=${LOG_LEVEL:-INFO}
LOG_DIR=/logs
EOF
    chown app:app /config/.env
fi

# Link configuration to app directory
if [ ! -L "/app/.env" ]; then
    log "Linking configuration file..."
    ln -sf /config/.env /app/.env
fi

# Set proper permissions for logs
chmod -R 755 /logs
chown -R app:app /logs

# Database migration on startup
log "Waiting for services to start before running migrations..."

# Function to wait for PostgreSQL
wait_for_postgres() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h localhost -p 5432 -U carscraping -q; then
            log "PostgreSQL is ready!"
            return 0
        fi
        warn "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "PostgreSQL failed to start within expected time"
    return 1
}

# Run database migrations in background after services start
{
    sleep 10  # Give supervisor time to start services
    
    if wait_for_postgres; then
        log "Running database migrations..."
        cd /app
        gosu app alembic upgrade head
        log "Database migrations completed!"
    else
        error "Could not connect to PostgreSQL for migrations"
    fi
} &

log "Starting services with supervisord..."

# Execute the main command
exec "$@"