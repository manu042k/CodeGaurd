"""Git repository cloning and management."""
import git
import shutil
from pathlib import Path
from typing import Optional, List
from loguru import logger

from config import settings


class GitManager:
    """Handles Git repository operations."""
    
    def __init__(self, repos_path: str = None):
        self.repos_path = Path(repos_path or settings.repos_path)
        self.repos_path.mkdir(parents=True, exist_ok=True)
    
    def clone_repository(self, repo_url: str, force: bool = False) -> tuple[str, str, str]:
        """
        Clone a Git repository.
        
        Returns:
            Tuple of (local_path, repo_name, commit_hash)
        """
        # Extract repo name from URL
        repo_name = self._extract_repo_name(repo_url)
        local_path = self.repos_path / repo_name
        
        # Check if already exists
        if local_path.exists():
            if force:
                logger.info(f"Removing existing repository: {local_path}")
                shutil.rmtree(local_path)
            else:
                logger.info(f"Repository already exists: {local_path}")
                return self._get_repo_info(local_path, repo_name)
        
        # Clone repository
        logger.info(f"Cloning repository: {repo_url}")
        try:
            repo = git.Repo.clone_from(repo_url, local_path, depth=1)
            commit_hash = repo.head.commit.hexsha
            logger.info(f"Repository cloned successfully: {repo_name} ({commit_hash[:8]})")
            return str(local_path), repo_name, commit_hash
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def _get_repo_info(self, local_path: Path, repo_name: str) -> tuple[str, str, str]:
        """Get info from existing repo."""
        try:
            repo = git.Repo(local_path)
            commit_hash = repo.head.commit.hexsha
            return str(local_path), repo_name, commit_hash
        except Exception as e:
            logger.warning(f"Could not read git info: {e}")
            return str(local_path), repo_name, "unknown"
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        # Handle various Git URL formats
        # https://github.com/user/repo.git -> repo
        # git@github.com:user/repo.git -> repo
        name = repo_url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name
    
    def get_code_files(self, repo_path: str) -> List[str]:
        """Get all code files from repository."""
        repo_path = Path(repo_path)
        code_files = []
        
        excluded_patterns = settings.excluded_patterns
        code_extensions = settings.code_extensions
        
        for file_path in repo_path.rglob('*'):
            # Skip if not a file
            if not file_path.is_file():
                continue
            
            # Skip excluded patterns
            relative_path = str(file_path.relative_to(repo_path))
            if any(pattern.rstrip('/') in relative_path for pattern in excluded_patterns):
                continue
            
            # Check if it's a code file
            if file_path.suffix.lower() in code_extensions:
                code_files.append(str(file_path))
        
        logger.info(f"Found {len(code_files)} code files in {repo_path.name}")
        return code_files
    
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
        }
        
        return language_map.get(ext, 'unknown')
