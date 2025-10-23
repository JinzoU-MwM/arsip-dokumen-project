#!/bin/bash

# AI Legal Document Automation - Development Startup Script

set -e

echo "🚀 Starting AI Legal Document Automation System (Development Mode)"
echo "================================================================"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p watched queue logs config

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing."
    echo "    Required: WAHA_API_KEY, Google Drive credentials, etc."
    read -p "Press Enter to continue or Ctrl+C to configure .env first..."
fi

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building custom service images..."
docker-compose build

# Start infrastructure services first
echo "🗄️  Starting infrastructure services (Database, Redis, Ollama)..."
docker-compose up -d postgres redis ollama

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start"
        exit 1
    fi
    sleep 2
done

for i in {1..30}; do
    if curl -f http://localhost:6379 &> /dev/null; then
        echo "✅ Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Redis failed to start"
        exit 1
    fi
    sleep 2
done

# Start application services
echo "🚀 Starting application services..."
docker-compose up -d waha document-watcher ai-processor notification-service

# Wait for application services
echo "⏳ Waiting for application services to be ready..."
sleep 15

# Start monitoring services
echo "📊 Starting monitoring services..."
docker-compose up -d prometheus grafana

# Check service health
echo "🏥 Checking all services health..."
SERVICES=("document-watcher:8001" "ai-processor:8002" "notification-service:8005" "waha:3000")

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    for i in {1..30}; do
        if curl -f http://localhost:$port/health &> /dev/null; then
            echo "✅ $name is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ $name failed to start"
        fi
        sleep 2
    done
done

# Start development services
echo "🛠️  Starting development services..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d pgadmin redis-commander

echo ""
echo "🎉 AI Legal Document Automation System is now running!"
echo "================================================================"
echo ""
echo "📋 Service URLs:"
echo "   Document Watcher API:    http://localhost:8001"
echo "   AI Processing API:        http://localhost:8002"
echo "   Notification API:         http://localhost:8005"
echo "   WhatsApp Service (WAHA):  http://localhost:3000"
echo "   Prometheus Monitoring:    http://localhost:9090"
echo "   Grafana Dashboard:        http://localhost:3001 (admin/admin)"
echo "   pgAdmin (Database):       http://localhost:5050"
echo "   Redis Commander:          http://localhost:8081"
echo ""
echo "📁 Watched Directories:"
echo "   Primary:  ./watched"
echo "   Secondary: ./queue"
echo ""
echo "🔧 Useful Commands:"
echo "   View logs:        docker-compose logs -f [service-name]"
echo "   Stop services:    docker-compose down"
echo "   Restart service:  docker-compose restart [service-name]"
echo "   Enter container:  docker-compose exec [service-name] bash"
echo ""
echo "📚 Documentation:   ./README.md"
echo "📊 Monitoring:       http://localhost:3001"
echo ""
echo "✨ Happy coding! Add documents to ./watched to test the system."