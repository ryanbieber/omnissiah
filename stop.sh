#!/bin/bash
# Stop Omnissiah services

echo "🛑 Stopping Omnissiah..."
docker-compose down

echo "✅ Services stopped."
echo ""
echo "To remove volumes (and all data):"
echo "  docker-compose down -v"
