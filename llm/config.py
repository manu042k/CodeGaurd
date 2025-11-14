"""Configuration management for LangGraph code analysis system."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    gemini_api_key: str = ""
    
    # Embedding Configuration
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dimension: int = 768
    max_chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Storage Paths (relative to project root for local development)
    sqlite_db_path: str = "data/codeguard.db"
    vector_index_path: str = "data/vectors.index"
    repos_path: str = "repos"
    models_path: str = "models"
    
    # Application Settings
    log_level: str = "INFO"
    api_port: int = 8001
    max_workers: int = 4
    
    # LLM Settings
    llm_model: str = "gemini-2.5-flash"  # Use stable model with better quota
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8000
    
    # Processing Settings
    batch_size: int = 32
    max_files_per_analysis: int = 1000
    excluded_patterns: list[str] = [
        "node_modules/",
        "__pycache__/",
        ".git/",
        "venv/",
        "env/",
        ".venv/",
        "dist/",
        "build/",
        "*.min.js",
        "*.bundle.js",
    ]
    
    # Code file extensions
    code_extensions: list[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".cpp", ".c", ".h", ".cs",
        ".go", ".rs", ".rb", ".php", ".swift",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def ensure_directories():
    """Ensure all required directories exist."""
    paths = [
        Path(settings.sqlite_db_path).parent,
        Path(settings.vector_index_path).parent,
        Path(settings.repos_path),
        Path(settings.models_path),
    ]
    
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
