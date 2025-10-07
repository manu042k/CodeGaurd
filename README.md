# CodeGuard

A local, self-hosted, LLM-powered static analysis platform that helps developers analyze their code repositories for quality, security, architecture, and documentation issues.

## 🎯 How It Works

When you click "Run Analysis" on a project:

```
1. 📦 Clone Repository
   ├─ Shallow clone from GitHub to /tmp
   └─ Extract metadata (size, commits, language)

2. 🤖 Multi-Agent Analysis (Parallel Execution)
   ├─ SecurityAgent       [Rule-based + LLM]
   ├─ DependencyAgent     [Rule-based + LLM]
   ├─ CodeQualityAgent    [Rule-based + LLM]
   ├─ PerformanceAgent    [Rule-based + LLM]
   └─ BestPracticesAgent  [Rule-based + LLM]

3. 📊 Aggregate & Score
   ├─ Combine findings from all agents
   ├─ Calculate overall score (0-100)
   └─ Categorize by severity

4. 🧹 Cleanup
   └─ Delete cloned repository

5. 📈 Display Report
   └─ Comprehensive multi-page report with insights
```

**See [docs/ANALYSIS_FLOW.md](docs/ANALYSIS_FLOW.md) for complete flow details.**

## Features

- 🔐 **GitHub SSO Authentication** - Secure login with your GitHub account
- 📊 **Multi-Agent Analysis** - Code Quality, Security, Architecture, and Documentation analysis
- 🎯 **Project Management** - Create and manage analysis projects from GitHub repositories
- 📈 **Interactive Reports** - Detailed analysis results with actionable insights
- 🐳 **Dockerized Deployment** - Easy setup with Docker Compose
- 🚀 **Real-time Analysis** - Background processing with live progress updates

## Tech Stack

### Frontend

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **React Icons** - Icon library

### Backend

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queue
- **Celery** - Background task processing
- **PyGithub** - GitHub API integration
- **JWT** - Authentication tokens

## Project Structure

```
├── frontend/              # Next.js frontend application
│   ├── src/app/          # App router pages
│   ├── src/components/   # Reusable React components
│   ├── src/lib/          # Utilities and API client
│   └── src/types/        # TypeScript type definitions
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── core/         # Core utilities (auth, config, database)
│   │   ├── models/       # SQLAlchemy models and Pydantic schemas
│   │   ├── routers/      # API route handlers
│   │   └── services/     # Business logic services
│   └── requirements.txt  # Python dependencies
├── docker-compose.yml    # Development environment
└── docs/                # Project documentation
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- GitHub account for OAuth setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/CodeGuard.git
cd CodeGuard
```

### 2. Set Up GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Create a new OAuth App with:
   - **Application name**: CodeGuard Local
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:8000/api/auth/github/callback`
3. Note down your Client ID and Client Secret

### 3. Run Setup Script

```bash
./dev-setup.sh
```

This will:

- Create necessary environment files
- Start Docker services (PostgreSQL, Redis)
- Install dependencies
- Set up the database

### 4. Configure Environment

Edit `backend/.env` and add your GitHub OAuth credentials:

```env
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
```

### 5. Start Development Servers

```bash
./start-dev.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 6. Access the Application

- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

## Development Workflow

1. **Sign in** with your GitHub account
2. **Connect repositories** from your GitHub account
3. **Create projects** to analyze specific repositories
4. **Run analyses** with configurable agents
5. **View reports** with detailed findings and recommendations

## API Endpoints

### Authentication

- `GET /api/auth/github/login` - Initiate GitHub OAuth
- `GET /api/auth/github/callback` - OAuth callback handler
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

### Projects

- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Analyses

- `POST /api/analyses` - Start new analysis
- `GET /api/analyses/{id}` - Get analysis results
- `GET /api/analyses/{id}/status` - Get analysis progress
- `DELETE /api/analyses/{id}` - Cancel analysis

### GitHub Integration

- `GET /api/github/repos` - List user repositories
- `GET /api/github/repos/{id}` - Get repository details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/your-username/CodeGuard/issues) on GitHub.
