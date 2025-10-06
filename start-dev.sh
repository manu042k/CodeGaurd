#!/bin/bash

# CodeGuard Development Start Script

echo "🚀 Starting CodeGuard with NextAuth Integration..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to kill background processes on exit
cleanup() {
    echo -e "\n🛑 Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Check if OAuth is configured
if [ ! -f frontend/.env.local ] || grep -q "your-github-client-id" frontend/.env.local; then
    echo -e "${YELLOW}⚠️  GitHub OAuth not configured!${NC}"
    echo "   Run ./setup-integration.sh first"
    exit 1
fi

# Start Docker services if available
if [ -f docker-compose.yml ]; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d db redis
    sleep 3
fi

# Start backend
echo -e "${GREEN}🔧 Starting backend server...${NC}"
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Services started!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait
