"""SQLite database manager for metadata and caching."""
import aiosqlite
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

from config import settings


class SQLiteManager:
    """Manages SQLite database for code analysis metadata."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.sqlite_db_path
        
    async def initialize(self):
        """Initialize database with schema."""
        await self._create_tables()
        logger.info(f"SQLite database initialized at {self.db_path}")
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS repositories (
            repo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL UNIQUE,
            repo_name TEXT NOT NULL,
            local_path TEXT NOT NULL,
            total_files INTEGER DEFAULT 0,
            total_size_bytes INTEGER DEFAULT 0,
            languages TEXT,  -- JSON array
            git_commit_hash TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_size INTEGER,
            language TEXT,
            file_type TEXT,
            priority_tier INTEGER DEFAULT 3,
            last_modified TIMESTAMP,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (repo_id) REFERENCES repositories(repo_id),
            UNIQUE(repo_id, file_path)
        );
        
        CREATE TABLE IF NOT EXISTS file_chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_type TEXT,
            content TEXT NOT NULL,
            start_line INTEGER,
            end_line INTEGER,
            entity_name TEXT,
            embedding_id INTEGER,
            token_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            UNIQUE(file_id, chunk_index)
        );
        
        CREATE TABLE IF NOT EXISTS embeddings_metadata (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            vector_dimension INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chunk_id) REFERENCES file_chunks(chunk_id)
        );
        
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL,
            query TEXT,
            results TEXT,  -- JSON
            execution_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (repo_id) REFERENCES repositories(repo_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_files_repo ON files(repo_id);
        CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);
        CREATE INDEX IF NOT EXISTS idx_chunks_file ON file_chunks(file_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON file_chunks(embedding_id);
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(schema)
            await db.commit()
    
    async def add_repository(self, repo_url: str, repo_name: str, local_path: str, 
                            git_commit_hash: str = None) -> int:
        """Add a repository to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO repositories (repo_url, repo_name, local_path, git_commit_hash)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(repo_url) DO UPDATE SET
                    local_path = excluded.local_path,
                    git_commit_hash = excluded.git_commit_hash,
                    indexed_at = CURRENT_TIMESTAMP
                RETURNING repo_id
                """,
                (repo_url, repo_name, local_path, git_commit_hash)
            )
            row = await cursor.fetchone()
            await db.commit()
            repo_id = row[0] if row else None
            
            if not repo_id:
                # Get existing repo_id
                cursor = await db.execute(
                    "SELECT repo_id FROM repositories WHERE repo_url = ?",
                    (repo_url,)
                )
                row = await cursor.fetchone()
                repo_id = row[0]
            
            logger.info(f"Repository added: {repo_name} (ID: {repo_id})")
            return repo_id
    
    async def add_file(self, repo_id: int, file_path: str, file_hash: str,
                      file_size: int, language: str, file_type: str = "source") -> int:
        """Add a file to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO files (repo_id, file_path, file_hash, file_size, language, file_type)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_id, file_path) DO UPDATE SET
                    file_hash = excluded.file_hash,
                    file_size = excluded.file_size,
                    indexed_at = CURRENT_TIMESTAMP
                RETURNING file_id
                """,
                (repo_id, file_path, file_hash, file_size, language, file_type)
            )
            row = await cursor.fetchone()
            await db.commit()
            
            file_id = row[0] if row else None
            if not file_id:
                cursor = await db.execute(
                    "SELECT file_id FROM files WHERE repo_id = ? AND file_path = ?",
                    (repo_id, file_path)
                )
                row = await cursor.fetchone()
                file_id = row[0]
            
            return file_id
    
    async def add_chunk(self, file_id: int, chunk_index: int, content: str,
                       chunk_type: str = "code", start_line: int = None,
                       end_line: int = None, entity_name: str = None,
                       token_count: int = None) -> int:
        """Add a code chunk to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO file_chunks 
                (file_id, chunk_index, content, chunk_type, start_line, end_line, entity_name, token_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id, chunk_index) DO UPDATE SET
                    content = excluded.content,
                    start_line = excluded.start_line,
                    end_line = excluded.end_line
                RETURNING chunk_id
                """,
                (file_id, chunk_index, content, chunk_type, start_line, end_line, entity_name, token_count)
            )
            row = await cursor.fetchone()
            await db.commit()
            return row[0] if row else None
    
    async def link_embedding(self, chunk_id: int, embedding_id: int, 
                            model_name: str, vector_dimension: int):
        """Link a chunk to its embedding."""
        async with aiosqlite.connect(self.db_path) as db:
            # Update chunk with embedding_id
            await db.execute(
                "UPDATE file_chunks SET embedding_id = ? WHERE chunk_id = ?",
                (embedding_id, chunk_id)
            )
            
            # Add embedding metadata
            await db.execute(
                """
                INSERT INTO embeddings_metadata (embedding_id, chunk_id, model_name, vector_dimension)
                VALUES (?, ?, ?, ?)
                """,
                (embedding_id, chunk_id, model_name, vector_dimension)
            )
            await db.commit()
    
    async def get_repository(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM repositories WHERE repo_url = ?",
                (repo_url,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_chunks_by_repo(self, repo_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """Get all chunks for a repository."""
        query = """
        SELECT 
            fc.chunk_id, fc.content, fc.chunk_type, fc.entity_name, 
            fc.embedding_id, f.file_path, f.language
        FROM file_chunks fc
        JOIN files f ON fc.file_id = f.file_id
        WHERE f.repo_id = ?
        ORDER BY f.file_path, fc.chunk_index
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (repo_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def save_analysis_session(self, repo_id: int, query: str, 
                                   results: Dict[str, Any], execution_time_ms: int):
        """Save an analysis session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO analysis_sessions (repo_id, query, results, execution_time_ms)
                VALUES (?, ?, ?, ?)
                """,
                (repo_id, query, json.dumps(results), execution_time_ms)
            )
            await db.commit()
    
    async def get_stats(self, repo_id: int) -> Dict[str, Any]:
        """Get statistics for a repository."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT 
                    COUNT(DISTINCT f.file_id) as total_files,
                    COUNT(fc.chunk_id) as total_chunks,
                    COUNT(DISTINCT fc.embedding_id) as embedded_chunks,
                    SUM(f.file_size) as total_size
                FROM files f
                LEFT JOIN file_chunks fc ON f.file_id = fc.file_id
                WHERE f.repo_id = ?
                """,
                (repo_id,)
            )
            row = await cursor.fetchone()
            return {
                "total_files": row[0] or 0,
                "total_chunks": row[1] or 0,
                "embedded_chunks": row[2] or 0,
                "total_size_bytes": row[3] or 0,
            }


def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()
