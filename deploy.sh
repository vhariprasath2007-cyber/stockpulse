#!/bin/bash
# StockPulse Docker Deployment Script

set -e

echo "🚀 StockPulse Docker Deployment"
echo "================================"

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your GEMINI_API_KEY"
    exit 1
fi

# Load environment variables
source .env

# Check for GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "❌ GEMINI_API_KEY not set in .env file"
    echo "📝 Please edit .env and add your GEMINI_API_KEY"
    exit 1
fi

echo "✅ Environment validated"

# Build and start containers
echo "🔨 Building containers..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check health
echo "🏥 Checking backend health..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is healthy"
        break
    fi
    echo "⏳ Waiting for backend... ($i/30)"
    sleep 2
done

# Final status
echo ""
echo "✅ StockPulse deployed successfully!"
echo ""
echo "📱 Frontend: http://localhost"
echo "🔌 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Stop:          docker compose down"
echo "  Restart:       docker compose restart"
echo "  Rebuild:       docker compose up -d --build"