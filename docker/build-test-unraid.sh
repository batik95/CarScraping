#!/bin/bash
# Build and test script for CarScraping Unraid container

set -e

echo "🏗️  Building CarScraping Unraid Container..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] $1${NC}"
}

# Build container
log "Building Docker image..."
docker build -f docker/Dockerfile.unraid -t carscraping:unraid .

# Create test directories
log "Creating test directories..."
mkdir -p ./test-unraid/{config,data,logs}

# Test container start
log "Testing container startup..."
docker run -d \
    --name carscraping-test \
    -p 18787:8787 \
    -v "$(pwd)/test-unraid/config:/config" \
    -v "$(pwd)/test-unraid/data:/data" \
    -v "$(pwd)/test-unraid/logs:/logs" \
    -e SCRAPING_INTERVAL=24 \
    -e LOG_LEVEL=INFO \
    -e DEBUG=false \
    carscraping:unraid

log "Waiting for container to initialize..."
sleep 30

# Check health
log "Checking health endpoint..."
if curl -f http://localhost:18787/health; then
    log "✅ Health check passed!"
else
    error "❌ Health check failed!"
    docker logs carscraping-test
fi

# Check logs
log "Checking logs..."
docker logs carscraping-test | tail -20

# Cleanup
log "Cleaning up test container..."
docker stop carscraping-test
docker rm carscraping-test

# Cleanup test directories
warn "Cleaning up test directories..."
rm -rf ./test-unraid

log "🎉 Build and test completed successfully!"
log "To push to Docker Hub: docker tag carscraping:unraid batik95/carscraping:unraid && docker push batik95/carscraping:unraid"