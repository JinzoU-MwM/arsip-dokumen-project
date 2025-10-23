# AI Legal Document Automation - Development Startup Script (PowerShell)

Write-Host "🚀 Starting AI Legal Document Automation System (Development Mode)" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

# Check if Docker is installed and running
try {
    $null = Get-Command docker -ErrorAction Stop
    $null = docker version -ErrorAction Stop
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    $null = Get-Command docker-compose -ErrorAction Stop
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "watched" | Out-Null
New-Item -ItemType Directory -Force -Path "queue" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "config" | Out-Null

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env file with your configuration before continuing." -ForegroundColor Yellow
    Write-Host "    Required: WAHA_API_KEY, Google Drive credentials, etc." -ForegroundColor Yellow
    $continue = Read-Host "Press Enter to continue or Ctrl+C to configure .env first"
}

# Pull latest images
Write-Host "📦 Pulling latest Docker images..." -ForegroundColor Yellow
docker-compose pull

# Build custom images
Write-Host "🔨 Building custom service images..." -ForegroundColor Yellow
docker-compose build

# Start infrastructure services first
Write-Host "🗄️  Starting infrastructure services (Database, Redis, Ollama)..." -ForegroundColor Yellow
docker-compose up -d postgres redis ollama

# Wait for infrastructure to be ready
Write-Host "⏳ Waiting for infrastructure services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if PostgreSQL is ready
Write-Host "🏥 Checking PostgreSQL health..." -ForegroundColor Yellow
$postgresReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $result = docker-compose exec -T postgres pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
            $postgresReady = $true
            break
        }
    } catch {
        # Continue trying
    }
    Start-Sleep -Seconds 2
}

if (-not $postgresReady) {
    Write-Host "❌ PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}

# Check if Redis is ready
Write-Host "🏥 Checking Redis health..." -ForegroundColor Yellow
$redisReady = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6379" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✅ Redis is ready" -ForegroundColor Green
        $redisReady = $true
        break
    } catch {
        # Redis might not have HTTP endpoint, check with docker-compose
        try {
            $null = docker-compose exec -T redis redis-cli ping 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Redis is ready" -ForegroundColor Green
                $redisReady = $true
                break
            }
        } catch {
            # Continue trying
        }
    }
    Start-Sleep -Seconds 2
}

if (-not $redisReady) {
    Write-Host "⚠️  Redis health check failed, but continuing..." -ForegroundColor Yellow
}

# Start application services
Write-Host "🚀 Starting application services..." -ForegroundColor Yellow
docker-compose up -d waha document-watcher ai-processor notification-service

# Wait for application services
Write-Host "⏳ Waiting for application services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Start monitoring services
Write-Host "📊 Starting monitoring services..." -ForegroundColor Yellow
docker-compose up -d prometheus grafana

# Check service health
Write-Host "🏥 Checking all services health..." -ForegroundColor Yellow
$services = @(
    @{Name="document-watcher"; Port=8001},
    @{Name="ai-processor"; Port=8002},
    @{Name="notification-service"; Port=8005},
    @{Name="waha"; Port=3000}
)

foreach ($service in $services) {
    $healthy = $false
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $($service.Name) is healthy" -ForegroundColor Green
                $healthy = $true
                break
            }
        } catch {
            # Continue trying
        }
        Start-Sleep -Seconds 2
    }

    if (-not $healthy) {
        Write-Host "❌ $($service.Name) failed to start" -ForegroundColor Red
    }
}

# Start development services
Write-Host "🛠️  Starting development services..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d pgadmin redis-commander

Write-Host ""
Write-Host "🎉 AI Legal Document Automation System is now running!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor Cyan
Write-Host "   Document Watcher API:    http://localhost:8001" -ForegroundColor White
Write-Host "   AI Processing API:        http://localhost:8002" -ForegroundColor White
Write-Host "   Notification API:         http://localhost:8005" -ForegroundColor White
Write-Host "   WhatsApp Service (WAHA):  http://localhost:3000" -ForegroundColor White
Write-Host "   Prometheus Monitoring:    http://localhost:9090" -ForegroundColor White
Write-Host "   Grafana Dashboard:        http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "   pgAdmin (Database):       http://localhost:5050" -ForegroundColor White
Write-Host "   Redis Commander:          http://localhost:8081" -ForegroundColor White
Write-Host ""
Write-Host "📁 Watched Directories:" -ForegroundColor Cyan
Write-Host "   Primary:  ./watched" -ForegroundColor White
Write-Host "   Secondary: ./queue" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs:        docker-compose logs -f [service-name]" -ForegroundColor Gray
Write-Host "   Stop services:    docker-compose down" -ForegroundColor Gray
Write-Host "   Restart service:  docker-compose restart [service-name]" -ForegroundColor Gray
Write-Host "   Enter container:  docker-compose exec [service-name] bash" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation:   ./README.md" -ForegroundColor Gray
Write-Host "📊 Monitoring:       http://localhost:3001" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Happy coding! Add documents to ./watched to test the system." -ForegroundColor Green