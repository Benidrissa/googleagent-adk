#!/bin/bash

# Launch script for Pregnancy Companion Agent
# This script sets up the environment and starts all Docker services

set -e

echo "🚀 Pregnancy Companion Agent - Launch Script"
echo "=============================================="
echo ""

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ ERROR: GOOGLE_API_KEY environment variable is not set!"
    echo ""
    echo "Please set your Google API key:"
    echo "  export GOOGLE_API_KEY='your_api_key_here'"
    echo ""
    echo "Or create a .env file with:"
    echo "  GOOGLE_API_KEY=your_api_key_here"
    echo ""
    exit 1
fi

echo "✅ GOOGLE_API_KEY is set"
echo ""

# Remove obsolete version attribute warning by creating temp file
echo "📝 Preparing docker-compose configuration..."
if grep -q "^version:" docker-compose.yml; then
    sed 's/^version:/#version:/' docker-compose.yml > docker-compose.tmp.yml
    mv docker-compose.tmp.yml docker-compose.yml
    echo "✅ Removed obsolete version attribute"
fi

# Stop any running containers
echo ""
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo ""
echo "🏗️  Building Docker images (this may take a few minutes)..."
echo ""
docker-compose build

echo ""
echo "🚀 Starting all services..."
echo ""
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="
docker-compose ps

# Check logs for errors
echo ""
echo "📋 Recent Logs:"
echo "==============="
docker-compose logs --tail=5

echo ""
echo "✅ Launch complete!"
echo ""
echo "🌐 Access Points:"
echo "  - Web Client:      http://localhost"
echo "  - API Endpoint:    http://localhost:8000"
echo "  - Traefik Dashboard: http://localhost:8080"
echo ""
echo "📝 Useful Commands:"
echo "  - View logs:       docker-compose logs -f"
echo "  - Stop services:   docker-compose down"
echo "  - Restart:         docker-compose restart"
echo "  - Check status:    docker-compose ps"
echo ""
