# CodeGuard 🛡️

**AI-Powered Code Analysis Platform**

CodeGuard is a comprehensive code analysis platform that leverages AI agents to provide detailed insights into your GitHub repositories. It performs multi-faceted analysis including security scanning, code quality assessment, architecture review, dependency management, and trend analysis.

## ✨ Features

### 🤖 AI-Powered Analysis Agents
- **Security Agent** - Identifies security vulnerabilities and potential threats
- **Code Quality Agent** - Analyzes code quality metrics and best practices
- **Architecture Agent** - Reviews architectural patterns and design decisions  
- **Dependency Agent** - Manages and analyzes project dependencies
- **Documentation Agent** - Evaluates documentation quality and coverage
- **Trend Agent** - Tracks development trends and patterns over time
- **Static Tool Agent** - Integrates with static analysis tools
- **Summary Agent** - Provides consolidated analysis reports
- **Supervisor Agent** - Orchestrates and coordinates all analysis agents

### 🔍 Comprehensive Code Insights
- Security vulnerability detection
- Code quality metrics and recommendations
- Architecture and design pattern analysis
- Dependency management and updates
- Documentation quality assessment
- Development trend analysis
- Static code analysis integration

### 🔐 GitHub Integration
- Seamless GitHub OAuth authentication
- Repository access and analysis
- Real-time synchronization with GitHub repositories
- Support for both public and private repositories

## 🏗️ Architecture

CodeGuard follows a modern microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  AI Agents      │
                       │  Multi-Agent    │
                       │  Analysis       │
                       └─────────────────┘
```

### Technology Stack

**Frontend:**
- Next.js 15.5.4 with React 19
- TypeScript for type safety
- Tailwind CSS for styling
- NextAuth.js for authentication
- React Icons for UI components

**Backend:**
- FastAPI for high-performance API
- SQLAlchemy for database ORM
- PostgreSQL for data persistence
- Python-JOSE for JWT handling
- PyGithub for GitHub API integration
- Pydantic for data validation

**Infrastructure:**
- Docker & Docker Compose for containerization
- CORS middleware for cross-origin requests
- Health check endpoints for monitoring

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- GitHub OAuth App (for authentication)
- Node.js 18+ (for development)
- Python 3.11+ (for backend development)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/CodeGaurd.git
cd CodeGaurd
```

### 2. Environment Setup
Create a `.env` file in the root directory:

```env
# Database Configuration
POSTGRES_DB=codeguard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
DATABASE_URL=postgresql://postgres:your_password_here@db:5432/codeguard

# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Security
SECRET_KEY=your_secret_key_here
NEXTAUTH_SECRET=your_nextauth_secret_here
NEXTAUTH_URL=http://localhost:3000

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=CodeGuard
```

### 3. GitHub OAuth Setup
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App with:
   - Application name: `CodeGuard`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:3000/api/auth/callback/github`
3. Copy the Client ID and Client Secret to your `.env` file

### 4. Start the Application
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Health Check
Verify the services are running:
```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
docker-compose exec db pg_isready -U postgres -d codeguard
```

## 📖 Usage

### Authentication
1. Navigate to http://localhost:3000
2. Click "Sign in with GitHub"
3. Authorize the CodeGuard application
4. You'll be redirected to the dashboard

### Repository Analysis
1. **Add Repository**: Connect your GitHub repositories
2. **Start Analysis**: Trigger comprehensive analysis using AI agents
3. **View Reports**: Review detailed analysis results and recommendations
4. **Track Trends**: Monitor code quality and security trends over time

### API Usage
The backend provides a comprehensive REST API:

```bash
# Get user projects
GET /api/v1/projects/

# Start analysis
POST /api/v1/analysis/start
{
  "repository_url": "https://github.com/user/repo",
  "analysis_type": "comprehensive"
}

# Get analysis results
GET /api/v1/analysis/{analysis_id}/results
```

## 🛠️ Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run full test suite
docker-compose -f docker-compose.test.yml up --build
```

## 📊 Monitoring

### Health Checks
- Backend: `GET /health`
- Database: Built-in PostgreSQL health checks
- Frontend: Next.js built-in health monitoring

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/yourusername/CodeGaurd/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/CodeGaurd/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/CodeGaurd/discussions)

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Next.js for the powerful React framework
- GitHub for the comprehensive API
- All contributors and open-source projects that made this possible

---

**CodeGuard** - Protecting your code with intelligent analysis 🛡️ 

## 🚧 Limitations

- **API Response Time**: API calls that trigger a full repository analysis can be time-consuming due to the comprehensive nature of the AI agents' analysis. We are actively working on optimizing this process, potentially through asynchronous background jobs.