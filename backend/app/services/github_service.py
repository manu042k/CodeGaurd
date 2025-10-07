from github import Github
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


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
