#!/bin/bash

# CarScraping Quick Start Script
# This script helps you get the CarScraping application running quickly

set -e

echo "🚗 CarScraping - Quick Start Setup"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   You can install it as a standalone tool (docker-compose) or as a Docker plugin (docker compose)."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. You can modify it if needed."
fi

# Create logs directory
mkdir -p logs
echo "📁 Created logs directory"

# Start the application
echo "🚀 Starting CarScraping application..."
echo "This will start PostgreSQL, Redis, and the main application."

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Unable to determine Docker Compose command."
    exit 1
fi

# Pull images and start services
$COMPOSE_CMD pull
$COMPOSE_CMD up -d

echo ""
echo "✅ CarScraping is starting up!"
echo ""
echo "🌐 Access the application at: http://localhost:8000"
echo "📊 Health check endpoint: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "  View logs:           $COMPOSE_CMD logs -f"
echo "  Stop application:    $COMPOSE_CMD down"
echo "  Restart:             $COMPOSE_CMD restart"
echo "  View status:         $COMPOSE_CMD ps"
echo ""
echo "⏳ The application may take a few moments to fully initialize..."
echo "   You can check the logs with: $COMPOSE_CMD logs -f app"