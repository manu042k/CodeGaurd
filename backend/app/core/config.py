from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/codeguard"
    
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

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    ENABLE_RATE_LIMITING: bool = True
    

    
    # Git Settings
    GIT_CLONE_TIMEOUT: int = 300  # 5 minutes
    
    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    
    class Config:
        env_file = ".env"

settings = Settings()
