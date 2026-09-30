<# 
.SYNOPSIS
    StockPulse Docker Deployment Script for Windows PowerShell

.DESCRIPTION
    Builds and deploys StockPulse using Docker Compose
#>

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Warning "⚠️  .env file not found. Creating from example..."
    Copy-Item ".env.example" ".env"
    Write-Host "📝 Please edit .env and add your GEMINI_API_KEY"
    exit 1
}

# Load environment variables
$envContent = Get-Content ".env" -Raw
$envLines = $envContent -split "`r?`n"
foreach ($line in $envLines) {
    if ($line -match '^\s*([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Check for GEMINI_API_KEY
if (-not $env:GEMINI_API_KEY -or $env:GEMINI_API_KEY -eq "your_gemini_api_key_here") {
    Write-Error "❌ GEMINI_API_KEY not set in .env file"
    Write-Host "📝 Please edit .env and add your GEMINI_API_KEY"
    exit 1
}

Write-Host "✅ Environment validated" -ForegroundColor Green

# Build and start containers
Write-Host "🔨 Building containers..." -ForegroundColor Cyan
docker compose build

Write-Host "🚀 Starting services..." -ForegroundColor Cyan
docker compose up -d

Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check health
Write-Host "🏥 Checking backend health..." -ForegroundColor Cyan
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is healthy" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "⏳ Waiting for backend... ($i/30)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "✅ StockPulse deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Frontend: http://localhost" -ForegroundColor Cyan
Write-Host "🔌 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Gray
Write-Host "  View logs:     docker compose logs -f" -ForegroundColor Gray
Write-Host "  Stop:          docker compose down" -ForegroundColor Gray
Write-Host "  Restart:       docker compose restart" -ForegroundColor Gray
Write-Host "  Rebuild:       docker compose up -d --build" -ForegroundColor Gray