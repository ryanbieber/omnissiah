#!/bin/bash
# Omnissiah Startup Script

set -e

echo "🚀 Starting Omnissiah..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your configuration."
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
docker-compose exec -T postgres pg_isready -U omnissiah || echo "⚠️  PostgreSQL not ready yet"

# Check FastAPI
echo "🔍 Checking FastAPI..."
curl -s http://localhost:8000/health || echo "⚠️  FastAPI not ready yet"

echo ""
echo "✅ Omnissiah is starting up!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo "💬 FastAPI: http://localhost:8000"
echo "🗄️  Database: localhost:5432"
echo ""
echo "Service Status:"
docker-compose ps
