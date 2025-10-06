#!/bin/bash

# CodeGuard Full Stack Integration Setup

echo "🚀 CodeGuard Full Stack Integration Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo -e "${BLUE}Checking $service_name on port $port...${NC}"
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not running${NC}"
        return 1
    fi
}

echo ""
echo "🔍 Checking Prerequisites"
echo "========================"

# Check if Docker is running (for backend services)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is running${NC}"
else
    echo -e "${YELLOW}⚠️  Docker is not running or not installed${NC}"
    echo "   Backend database and Redis services require Docker"
fi

# Check if Node.js is installed
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js is installed ($NODE_VERSION)${NC}"
else
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

# Check if Python is installed
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python is installed ($PYTHON_VERSION)${NC}"
else
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo ""
echo "🔧 Setting up Frontend OAuth Configuration"
echo "=========================================="

cd frontend

# Run OAuth setup if not already configured
if [ ! -f .env.local ] || ! grep -q "GITHUB_CLIENT_ID=" .env.local || grep -q "your-github-client-id" .env.local; then
    echo "Running OAuth setup..."
    ./setup-oauth.sh
    
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: You need to configure GitHub OAuth credentials${NC}"
    echo "   1. Go to: https://github.com/settings/developers"
    echo "   2. Create a new OAuth App with:"
    echo "      - Homepage URL: http://localhost:3000"
    echo "      - Callback URL: http://localhost:3000/api/auth/callback/github"
    echo "   3. Copy your Client ID and Secret to frontend/.env.local"
    echo ""
    read -p "Press Enter when you've configured GitHub OAuth credentials..."
else
    echo -e "${GREEN}✅ Frontend OAuth configuration exists${NC}"
fi

echo ""
echo "📦 Installing Frontend Dependencies"
echo "=================================="
npm install

cd ..

echo ""
echo "🐍 Setting up Backend Environment"
echo "================================"

cd backend

# Check if backend .env exists and has GitHub credentials
if [ ! -f .env ]; then
    echo "Creating backend .env file..."
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/codeguard

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub OAuth (you need to set these up with GitHub)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# JWT
SECRET_KEY=your-secret-key-change-this-in-production-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# API Settings
API_V1_STR=/api
PROJECT_NAME=CodeGuard API
EOF
fi

# Update backend .env with same GitHub credentials as frontend
FRONTEND_CLIENT_ID=$(grep "GITHUB_CLIENT_ID=" ../frontend/.env.local | cut -d'=' -f2)
FRONTEND_CLIENT_SECRET=$(grep "GITHUB_CLIENT_SECRET=" ../frontend/.env.local | cut -d'=' -f2)

if [ "$FRONTEND_CLIENT_ID" != "your-github-client-id" ] && [ -n "$FRONTEND_CLIENT_ID" ]; then
    echo "Syncing GitHub OAuth credentials with backend..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/GITHUB_CLIENT_ID=.*/GITHUB_CLIENT_ID=$FRONTEND_CLIENT_ID/" .env
        sed -i '' "s/GITHUB_CLIENT_SECRET=.*/GITHUB_CLIENT_SECRET=$FRONTEND_CLIENT_SECRET/" .env
    else
        sed -i "s/GITHUB_CLIENT_ID=.*/GITHUB_CLIENT_ID=$FRONTEND_CLIENT_ID/" .env
        sed -i "s/GITHUB_CLIENT_SECRET=.*/GITHUB_CLIENT_SECRET=$FRONTEND_CLIENT_SECRET/" .env
    fi
    echo -e "${GREEN}✅ GitHub OAuth credentials synced to backend${NC}"
fi

# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found${NC}"
fi

cd ..

echo ""
echo "🚢 Starting Services"
echo "==================="

# Start backend services (database, redis) if docker-compose exists
if [ -f docker-compose.yml ]; then
    echo "Starting backend services (database, redis)..."
    docker-compose up -d db redis
    sleep 5
    echo -e "${GREEN}✅ Backend services started${NC}"
fi

echo ""
echo "🔍 Service Status Check"
echo "======================"

# Check if services are running
check_service "Database" "5432" "postgres://postgres:password@localhost:5432/codeguard" || echo "   Run: docker-compose up -d db"
check_service "Redis" "6379" "redis://localhost:6379" || echo "   Run: docker-compose up -d redis"

echo ""
echo "🎯 Next Steps"
echo "============"
echo ""
echo "1. Start the Backend API:"
echo "   cd backend"
echo "   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. In another terminal, start the Frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser to:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔗 Integration Features:"
echo "• NextAuth handles OAuth in frontend"
echo "• Backend API provides data and analysis"
echo "• Automatic user sync between systems"
echo "• JWT tokens for backend API access"
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📖 For troubleshooting, see:"
echo "   frontend/README_OAUTH_FIXED.md"
echo "   frontend/OAUTH_SETUP.md"
