from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/codeguard"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "CodeGuard API"
    
    # File Storage
    UPLOAD_DIR: str = "/tmp/codeguard/uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Analysis Settings
    MAX_ANALYSIS_TIME: int = 3600  # 1 hour
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "gemini"  # Options: openai, anthropic, gemini
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-pro"  # or gemini-2.5-flash
    
    # Repository Analysis Settings
    MAX_FILE_SIZE_MB: int = 1  # Skip files larger than this
    MAX_FILES_PER_ANALYSIS: int = 100  # Maximum files to analyze
    CHUNK_SIZE: int = 100000  # Characters per chunk for large files
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    ENABLE_RATE_LIMITING: bool = True
    
    # Git Settings
    GIT_CLONE_TIMEOUT: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"

settings = Settings()
