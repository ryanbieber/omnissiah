.PHONY: up down down-v logs logs-fast logs-api logs-postgres logs-react clean help ps restart build

# Default target
help:
	@echo "Omnissiah Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "make up                  Start all services"
	@echo "make down                Stop services (preserve data)"
	@echo "make down-v              Stop services and wipe database"
	@echo "make restart             Restart all services"
	@echo "make build               Build Docker images"
	@echo "make ps                  Show running containers"
	@echo "make logs                Show logs from all services"
	@echo "make logs-fast           Show logs (no timestamps)"
	@echo "make logs-api            Show FastAPI logs"
	@echo "make logs-postgres       Show PostgreSQL logs"
	@echo "make logs-react          Show React logs"
	@echo "make clean               Clean up containers and images"
	@echo "make db-shell            Open PostgreSQL shell"
	@echo "make api-shell           Open FastAPI container shell"
	@echo ""

# Start all services
up:
	@echo "🚀 Starting Omnissiah..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "📱 Access Points:"
	@echo "  Dashboard:   http://localhost:3000"
	@echo "  API Docs:    http://localhost:8000/api/docs"
	@echo "  Health:      http://localhost:8000/health"
	@echo ""

# Stop services (preserve data)
down:
	@echo "🛑 Stopping Omnissiah..."
	docker compose down
	@echo "✅ Services stopped (data preserved)"

# Stop services and wipe database
down-v:
	@echo "⚠️  WARNING: This will delete all data!"
	@echo "🛑 Stopping services and removing volumes..."
	docker compose down -v
	@echo "✅ Services stopped and database wiped"

# Restart services
restart: down up

# Build Docker images
build:
	@echo "🏗️  Building Docker images..."
	docker compose build
	@echo "✅ Build complete"

# Show running containers
ps:
	@echo "📦 Running Containers:"
	@docker compose ps

# View all logs
logs:
	@docker compose logs -f --timestamps

# View logs without timestamps
logs-fast:
	@docker compose logs -f

# View FastAPI logs
logs-api:
	@docker compose logs -f fastapi

# View PostgreSQL logs
logs-postgres:
	@docker compose logs -f postgres

# View React logs
logs-react:
	@docker compose logs -f react

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Open PostgreSQL shell
db-shell:
	@echo "🗄️  Connecting to PostgreSQL..."
	docker compose exec postgres psql -U omnissiah -d omnissiah

# Open FastAPI container shell
api-shell:
	@echo "🔧 Connecting to FastAPI container..."
	docker compose exec fastapi /bin/bash

# Health check
health:
	@echo "🔍 Checking service health..."
	@echo ""
	@echo "FastAPI:"
	@curl -s http://localhost:8000/health || echo "❌ Not responding"
	@echo ""
	@echo "PostgreSQL:"
	@docker compose exec postgres pg_isready -U omnissiah -d omnissiah || echo "❌ Not responding"
	@echo ""

# Status summary
status: ps health

# Development mode (rebuild and restart)
dev:
	@echo "🔄 Rebuilding and restarting in development mode..."
	docker compose up -d --build
	@echo "✅ Development environment ready"

# Production build
prod:
	@echo "📦 Building for production..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "✅ Production build complete"
