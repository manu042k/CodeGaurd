from github import Github
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.config import settings
import logging
import git
import os
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CloneResult:
    """Result of a repository clone operation"""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None
    size_mb: float = 0.0
    duration_seconds: float = 0.0
    commit_count: Optional[int] = None


class GitHubService:
    def __init__(self, access_token: str, db: Session = None):
        self.db = db
        self.github = Github(access_token)
        self.access_token = access_token
    
    def get_repo_details(self, full_name: str) -> Dict[str, Any]:
        """Get repository details from GitHub by full name."""
        try:
            repo = self.github.get_repo(full_name)
            return {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "private": repo.private,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url,
            }
        except Exception as e:
            logger.error(f"Error fetching repo details for {full_name}: {str(e)}")
            raise ValueError(f"Could not fetch repository details for {full_name}")

    def get_user_repositories(self, user_id: str, db: Session = None) -> List[Dict[str, Any]]:
        """Fetch user repositories from GitHub and return as a list of dicts"""
        try:
            github_user = self.github.get_user()
            repos = github_user.get_repos(sort="updated", direction="desc")
            
            repositories = []
            
            for repo in repos:
                repositories.append({
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "html_url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "language": repo.language,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "owner_login": repo.owner.login,
                    "owner_avatar_url": repo.owner.avatar_url,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                })
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            raise

    def validate_repository_access_by_name(self, full_name: str) -> bool:
        """Validate that user has access to the repository by its full name."""
        try:
            repo = self.github.get_repo(full_name)
            _ = repo.name  # Accessing an attribute to trigger potential exception
            return True
        except Exception:
            return False
    
    def get_user(self) -> Optional[dict]:
        """Get GitHub user information"""
        try:
            user = self.github.get_user()
            return {
                "id": user.id,
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url
            }
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            return None

    def clone_repository(
        self,
        repository: Dict[str, Any],
        target_path: str,
        shallow: bool = True,
        depth: Optional[int] = 1,
    ) -> CloneResult:
        """
        Clone a GitHub repository to the specified path
        
        Args:
            repository: Repository info dict with clone_url, private, etc.
            target_path: Path where to clone the repository
            shallow: Whether to do shallow clone
            depth: Depth for shallow clone
            
        Returns:
            CloneResult with success status and metadata
        """
        start_time = time.time()
        clone_url = repository.get("clone_url")
        
        if not clone_url:
            return CloneResult(
                success=False,
                error="No clone URL provided",
                duration_seconds=time.time() - start_time,
            )
        
        # Modify URL for private repos
        if repository.get("private", False):
            token = self.access_token
            clone_url = clone_url.replace("https://", f"https://oauth2:{token}@")
            logger.info("Using authenticated clone URL for private repository.")
        
        try:
            logger.info(f"Cloning from {clone_url} to {target_path}")
            
            # Ensure target directory exists
            os.makedirs(target_path, exist_ok=True)
            
            # Clone the repository
            if shallow and depth:
                repo = git.Repo.clone_from(clone_url, target_path, depth=depth)
            else:
                repo = git.Repo.clone_from(clone_url, target_path)
            
            # Get repository size
            size_mb = self._get_directory_size_mb(target_path)
            
            # Get commit count
            try:
                commit_count = len(list(repo.iter_commits()))
            except:
                commit_count = None
            
            duration = time.time() - start_time
            
            logger.info(
                f"Successfully cloned repository to {target_path} "
                f"({size_mb:.2f} MB, {commit_count or '?'} commits) in {duration:.2f}s"
            )
            
            return CloneResult(
                success=True,
                path=target_path,
                size_mb=size_mb,
                duration_seconds=duration,
                commit_count=commit_count,
            )
            
        except git.exc.GitCommandError as e:
            duration = time.time() - start_time
            error_msg = f"Git clone failed: {e.stderr}"
            logger.error(error_msg)
            return CloneResult(
                success=False,
                error=error_msg,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Clone failed: {str(e)}"
            logger.error(error_msg)
            return CloneResult(
                success=False,
                error=error_msg,
                duration_seconds=duration,
            )
    
    def _get_directory_size_mb(self, path: str) -> float:
        """Calculate directory size in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size / (1024 * 1024)
