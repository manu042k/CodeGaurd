# Environment Setup

This project uses a **single `.env` file** for all environment configuration across all services.

## Quick Setup

1. The `.env` file is already created with your GitHub credentials
2. All Docker Compose services will automatically load from this single `.env` file
3. No additional configuration needed for development

## Current Configuration

The `.env` file contains:

- ✅ **GitHub OAuth**: Your actual GitHub app credentials
- ✅ **Authentication**: NextAuth and JWT secrets
- ✅ **Database**: PostgreSQL configuration for Docker
- ✅ **Redis**: Redis configuration for caching and Celery tasks

## How It Works

```
.env                    # Single environment file (loaded by all services)
├── Frontend service    # Uses GITHUB_CLIENT_ID, NEXTAUTH_SECRET, etc.
├── Backend service     # Uses DATABASE_URL, SECRET_KEY, etc.
├── Database service    # Uses POSTGRES_DB, POSTGRES_USER, etc.
└── Celery service      # Uses CELERY_BROKER_URL, etc.
```

## Docker Compose Integration

All services in `docker-compose.yml` use:

```yaml
env_file:
  - .env
```

This means:

- **One source of truth** for all environment variables
- **No duplication** across multiple env files
- **Consistent configuration** across all services

## Security Notes

- The `.env` file is in `.gitignore` (not committed to version control)
- Use `.env.example` as a template for new environments
- All secrets are centralized in one place
