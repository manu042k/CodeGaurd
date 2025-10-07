from github import Github
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.database import Repository, User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, access_token: str, db: Session = None):
        self.db = db
        self.github = Github(access_token)
        self.access_token = access_token
    
    def get_user_repositories(self, user_id: str, db: Session = None) -> List[Repository]:
        """Fetch and sync user repositories from GitHub"""
        try:
            if db is None:
                db = self.db
                
            # Use the access token to get repositories
            github_user = self.github.get_user()
            repos = github_user.get_repos(sort="updated", direction="desc")
            
            repositories = []
            
            for repo in repos:
                # Check if repository already exists in our database
                db_repo = db.query(Repository).filter(Repository.id == repo.id).first()
                
                if not db_repo:
                    # Create new repository record
                    db_repo = Repository(
                        id=repo.id,
                        name=repo.name,
                        full_name=repo.full_name,
                        description=repo.description,
                        private=repo.private,
                        html_url=repo.html_url,
                        clone_url=repo.clone_url,
                        language=repo.language,
                        stargazers_count=repo.stargazers_count,
                        forks_count=repo.forks_count,
                        owner_login=repo.owner.login,
                        owner_avatar_url=repo.owner.avatar_url,
                        created_at=repo.created_at,
                        updated_at=repo.updated_at
                    )
                    db.add(db_repo)
                else:
                    # Update existing repository
                    db_repo.name = repo.name
                    db_repo.full_name = repo.full_name
                    db_repo.description = repo.description
                    db_repo.private = repo.private
                    db_repo.html_url = repo.html_url
                    db_repo.clone_url = repo.clone_url
                    db_repo.language = repo.language
                    db_repo.stargazers_count = repo.stargazers_count
                    db_repo.forks_count = repo.forks_count
                    db_repo.owner_login = repo.owner.login
                    db_repo.owner_avatar_url = repo.owner.avatar_url
                    db_repo.updated_at = repo.updated_at
                
                repositories.append(db_repo)
            
            db.commit()
            return repositories
            
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            db.rollback()
            raise
    
    def get_repository_by_id(self, repo_id: int) -> Optional[Repository]:
        """Get repository by GitHub ID"""
        return self.db.query(Repository).filter(Repository.id == repo_id).first()
    
    def validate_repository_access(self, repo_id: int, user_id: str) -> bool:
        """Validate that user has access to the repository"""
        try:
            # First check if repository exists in our database
            if self.db:
                repository = self.db.query(Repository).filter(Repository.id == repo_id).first()
                if repository:
                    # Use the full_name to validate access
                    github = Github(self.access_token)
                    repo = github.get_repo(repository.full_name)
                    _ = repo.name  # This will raise an exception if no access
                    return True
            
            # Fallback: try to get repo by ID directly (less reliable)
            try:
                github_user = self.github.get_user()
                repos = github_user.get_repos()
                for repo in repos:
                    if repo.id == repo_id:
                        return True
                return False
            except:
                return False
            
        except Exception as e:
            logger.error(f"Repository access validation failed for repo {repo_id}: {str(e)}")
            return False
            
    def validate_repository_access_by_name(self, full_name: str) -> bool:
        """Validate repository access using full name (e.g., 'user/repo')"""
        try:
            github = Github(self.access_token)
            repo = github.get_repo(full_name)
            # Try to access the repository - will raise exception if no access
            _ = repo.name
            return True
        except Exception as e:
            logger.error(f"Repository access validation failed for {full_name}: {str(e)}")
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
