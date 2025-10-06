# CodeGuard - Full Stack Integration Guide

## 🎯 Overview

CodeGuard now uses a **hybrid authentication approach** that combines the best of both worlds:

- **Frontend**: NextAuth.js for OAuth flow and session management
- **Backend**: FastAPI with JWT tokens for secure API access
- **Integration**: Automatic user sync and token exchange

## 🔧 Architecture

```
┌─────────────────┐    NextAuth     ┌─────────────────┐
│                 │ ◄─────────────► │                 │
│    Frontend     │                 │     GitHub      │
│   (Next.js)     │                 │     OAuth       │
│                 │                 │                 │
└─────────┬───────┘                 └─────────────────┘
          │
          │ API Calls with JWT
          │
          ▼
┌─────────────────┐                 ┌─────────────────┐
│                 │                 │                 │
│    Backend      │ ◄─────────────► │   Database      │
│   (FastAPI)     │                 │ (PostgreSQL)    │
│                 │                 │                 │
└─────────────────┘                 └─────────────────┘
```

## 🚀 Quick Start

### 1. Run the Integration Setup

```bash
./setup-integration.sh
```

### 2. Configure GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create new OAuth App:
   - **Application name**: `CodeGuard Development`
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`
3. Copy credentials to `frontend/.env.local`

### 3. Start the Development Environment

```bash
./start-dev.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🔐 How Authentication Works

### 1. User Sign-In Flow

1. User clicks "Sign in with GitHub" on frontend
2. NextAuth redirects to GitHub OAuth
3. GitHub redirects back to NextAuth callback
4. NextAuth creates session and calls backend `/auth/sync-user`
5. Backend creates/updates user and returns JWT token
6. Frontend session includes both NextAuth data and backend JWT

### 2. API Requests

- Frontend uses NextAuth session for UI state
- Backend API calls use JWT token from session
- Automatic token refresh handled by NextAuth

### 3. Protected Routes

- Frontend: Middleware protects `/dashboard`, `/projects`, etc.
- Backend: JWT verification on protected endpoints

## 📁 File Structure

```
CodeGuard/
├── frontend/
│   ├── src/app/api/auth/[...nextauth]/route.ts  # NextAuth config
│   ├── src/lib/backend-api.ts                   # Backend API client
│   ├── middleware.ts                            # Route protection
│   ├── .env.local                               # Frontend config
│   └── setup-oauth.sh                           # OAuth setup script
├── backend/
│   ├── app/routers/auth.py                      # Auth endpoints
│   ├── app/core/config.py                       # Backend config
│   └── .env                                     # Backend config
├── setup-integration.sh                         # Full setup script
└── start-dev.sh                                 # Dev server script
```

## 🔗 API Endpoints

### Frontend (NextAuth)

- `GET /api/auth/signin` - Sign in page
- `GET /api/auth/callback/github` - OAuth callback
- `GET /api/auth/session` - Current session

### Backend (FastAPI)

- `POST /api/auth/sync-user` - Sync user from NextAuth
- `GET /api/auth/me` - Get current user
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/github/repos` - List GitHub repos

## ⚙️ Configuration

### Frontend Environment (`.env.local`)

```env
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Environment (`.env`)

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/codeguard

# GitHub OAuth (same as frontend)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# JWT
SECRET_KEY=your-backend-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## 🔍 Troubleshooting

### OAuth Issues

- **"redirect_uri_mismatch"**: Ensure GitHub app callback URL is exactly `http://localhost:3000/api/auth/callback/github`
- **"Invalid client"**: Verify `GITHUB_CLIENT_ID` matches your GitHub app
- **"Bad verification code"**: Check `GITHUB_CLIENT_SECRET` is correct

### Backend Connection Issues

- **"Failed to sync user"**: Backend server not running on port 8000
- **"Invalid JWT"**: Check backend `SECRET_KEY` configuration
- **"CORS error"**: Verify backend `CORS_ORIGINS` includes frontend URL

### Database Issues

- **Connection failed**: Run `docker-compose up -d db redis`
- **Tables not found**: Backend will auto-create tables on startup

## 🧪 Testing the Integration

### 1. Test OAuth Flow

1. Visit `http://localhost:3000`
2. Click "Sign in with GitHub"
3. Complete GitHub OAuth
4. Should redirect to dashboard with user info

### 2. Test Backend API

1. Sign in via frontend
2. Open browser dev tools → Network tab
3. Navigate to dashboard
4. Should see API calls to `localhost:8000` with Authorization headers

### 3. Test Protected Routes

1. Sign out
2. Try to visit `http://localhost:3000/dashboard`
3. Should redirect to sign-in page

## 🚀 Production Deployment

### Environment Updates

```env
# Frontend
NEXTAUTH_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# Backend
CORS_ORIGINS=["https://your-domain.com"]
DATABASE_URL=your-production-database-url
```

### GitHub OAuth App

Update OAuth app settings:

- **Homepage URL**: `https://your-domain.com`
- **Callback URL**: `https://your-domain.com/api/auth/callback/github`

## ✅ Features Working

- ✅ **NextAuth OAuth Flow**: GitHub sign-in with proper callback handling
- ✅ **Backend Integration**: Automatic user sync and JWT token generation
- ✅ **API Authentication**: Secure backend API calls with JWT tokens
- ✅ **Route Protection**: Frontend middleware protecting authenticated routes
- ✅ **Session Management**: Persistent sessions with NextAuth
- ✅ **Error Handling**: Comprehensive error pages and user feedback
- ✅ **Development Tools**: Setup scripts and integration testing

## 📖 Next Steps

1. **Customize Dashboard**: Add your specific project metrics and data
2. **Add Features**: Implement project creation, GitHub import, security analysis
3. **Enhance UI**: Customize the design to match your brand
4. **Add Tests**: Write integration tests for the auth flow and API endpoints
5. **Deploy**: Configure production environment and deploy to your hosting platform

The OAuth configuration issues have been completely resolved, and you now have a robust, secure authentication system that works seamlessly between your frontend and backend!
