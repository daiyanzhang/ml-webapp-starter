#!/bin/bash

echo "🚀 Starting development environment..."

# Stop any existing services
echo "🧹 Cleaning up existing services..."
docker-compose down 2>/dev/null
docker-compose -f docker-compose.dev.yml down 2>/dev/null

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
timeout=60
counter=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
    echo -n "."
done
echo ""

# Initialize admin user (skip if --skip-init flag is provided)
if [[ "$1" != "--skip-init" ]]; then
    echo "👤 Initializing admin user..."
    docker-compose -f docker-compose.dev.yml exec backend-debug python /scripts/create_admin.py
else
    echo "⏭️  Skipping admin user initialization"
fi

echo ""
echo "✅ Development environment ready!"
echo ""
echo "🌐 Access URLs:"
echo "  Frontend:      http://localhost:3000"
echo "  Backend API:   http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Storybook:     http://localhost:6006"
echo "  Temporal Web:  http://localhost:8080"
echo "  Ray Dashboard: http://localhost:8265"
echo ""
echo "📊 Development Tools:"
echo "  ./scripts/dev-logs-iterm.sh    # 4-quadrant logs with perfect text selection"
echo ""
echo "💡 Tip: Use './scripts/dev-start.sh --skip-init' to skip admin user creation"
echo ""