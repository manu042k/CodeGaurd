#!/bin/bash

# CodeGuard Docker Integration Test Script

echo "🐳 CodeGuard Docker Integration Test"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}Waiting for $service_name to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "healthy\|Up"; then
            echo -e "${GREEN}✅ $service_name is healthy${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for $service_name...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to become healthy${NC}"
    return 1
}

# Function to test HTTP endpoint
test_endpoint() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -e "${BLUE}Testing $service_name endpoint: $url${NC}"
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $service_name endpoint is responding (HTTP $status_code)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name endpoint failed (HTTP $status_code, expected $expected_status)${NC}"
        return 1
    fi
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Creating from template...${NC}"
    cat > .env << 'EOF'
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# NextAuth Configuration
NEXTAUTH_SECRET=your-nextauth-secret

# Backend Configuration
SECRET_KEY=your-backend-secret-key
EOF
    echo -e "${YELLOW}⚠️  Please update .env with your actual credentials${NC}"
fi

echo ""
echo "🚀 Starting Docker services..."
echo "=============================="

# Stop any existing containers
docker-compose down

# Build and start services
echo -e "${BLUE}Building and starting services...${NC}"
docker-compose up -d --build

echo ""
echo "🔍 Checking service health..."
echo "============================="

# Wait for services to be healthy
if ! check_service_health "db"; then
    echo -e "${RED}Database failed to start${NC}"
    docker-compose logs db
    exit 1
fi

if ! check_service_health "redis"; then
    echo -e "${RED}Redis failed to start${NC}"
    docker-compose logs redis
    exit 1
fi

if ! check_service_health "backend"; then
    echo -e "${RED}Backend failed to start${NC}"
    docker-compose logs backend
    exit 1
fi

if ! check_service_health "frontend"; then
    echo -e "${RED}Frontend failed to start${NC}"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🧪 Running integration tests..."
echo "==============================="

# Wait a moment for services to fully initialize
sleep 5

# Test backend API
if test_endpoint "Backend API" "http://localhost:8000/health"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Backend logs:"
    docker-compose logs --tail=20 backend
fi

# Test backend API docs
if test_endpoint "Backend API Docs" "http://localhost:8000/docs"; then
    echo -e "${GREEN}✅ Backend API documentation is accessible${NC}"
else
    echo -e "${RED}❌ Backend API documentation is not accessible${NC}"
fi

# Test frontend
if test_endpoint "Frontend" "http://localhost:3000"; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend is not accessible${NC}"
    echo "Frontend logs:"
    docker-compose logs --tail=20 frontend
fi

# Test NextAuth endpoints
if test_endpoint "NextAuth API" "http://localhost:3000/api/auth/providers"; then
    echo -e "${GREEN}✅ NextAuth API is working${NC}"
else
    echo -e "${RED}❌ NextAuth API is not working${NC}"
fi

echo ""
echo "📊 Service Status Summary"
echo "========================"

# Show container status
docker-compose ps

echo ""
echo "📋 Test Results"
echo "==============="

# Count running services
running_services=$(docker-compose ps --services --filter "status=running" | wc -l)
total_services=$(docker-compose ps --services | wc -l)

echo -e "Services running: ${GREEN}$running_services${NC}/$total_services"

if [ "$running_services" -eq "$total_services" ]; then
    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may have issues${NC}"
fi

echo ""
echo "🌐 Access URLs"
echo "=============="
echo "Frontend:        http://localhost:3000"
echo "Backend API:     http://localhost:8000"
echo "API Docs:        http://localhost:8000/docs"
echo "NextAuth:        http://localhost:3000/api/auth/signin"

echo ""
echo "🔧 Useful Commands"
echo "=================="
echo "View logs:       docker-compose logs [service_name]"
echo "Stop services:   docker-compose down"
echo "Restart:         docker-compose restart [service_name]"
echo "Shell access:    docker-compose exec [service_name] /bin/bash"

echo ""
echo -e "${GREEN}✅ Docker integration test completed!${NC}"

# Optional: Open browser
if command -v open >/dev/null 2>&1; then
    echo ""
    read -p "Open frontend in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:3000
    fi
fi
