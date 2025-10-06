from github import Github
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.database import Repository, User
from app.core.config import settings
import logging
import os
import shutil
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CloneError(Exception):
    """Base exception for repository cloning errors"""
    pass


class CloneTimeoutError(CloneError):
    """Raised when cloning exceeds timeout"""
    pass


class CloneAuthenticationError(CloneError):
    """Raised when authentication fails during clone"""
    pass


class CloneNetworkError(CloneError):
    """Raised when network issues occur during clone"""
    pass


@dataclass
class CloneResult:
    """Result of a repository clone operation"""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None
    size_mb: Optional[float] = None
    duration_seconds: Optional[float] = None
    commit_count: Optional[int] = None

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
    
    def clone_repository(
        self, 
        repository: Repository, 
        target_path: str,
        shallow: bool = False,
        depth: int = 1,
        timeout: int = 600,
        cleanup_on_failure: bool = True
    ) -> CloneResult:
        """
        Clone a repository to local filesystem with robust error handling.
        
        This is the single entry point for all repository cloning operations.
        Supports both public and private repositories with authentication.
        
        Args:
            repository: Repository object from database
            target_path: Target path for cloning
            shallow: If True, perform shallow clone (faster, less history)
            depth: Depth for shallow clone (default: 1)
            timeout: Timeout in seconds for clone operation (default: 600)
            cleanup_on_failure: If True, remove partial clone on failure
            
        Returns:
            CloneResult: Object containing success status, path, error details, and metadata
            
        Raises:
            CloneError: Base exception for cloning errors
            CloneTimeoutError: When clone operation exceeds timeout
            CloneAuthenticationError: When authentication fails
            CloneNetworkError: When network issues occur
        """
        import git
        import time
        from git.exc import GitCommandError
        
        start_time = time.time()
        clone_url = None
        
        try:
            # Validate inputs
            if not repository:
                raise CloneError("Repository object is None")
            
            if not repository.clone_url:
                raise CloneError(f"Repository {repository.full_name} has no clone URL")
            
            # Prepare clone URL with authentication
            clone_url = self._prepare_clone_url(repository)
            
            # Ensure target path is absolute
            target_path = os.path.abspath(target_path)
            
            # Check if target already exists
            if os.path.exists(target_path):
                if os.listdir(target_path):
                    logger.warning(f"Target path {target_path} already exists and is not empty")
                    # Clean it up
                    shutil.rmtree(target_path, ignore_errors=True)
            
            # Create parent directory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            logger.info(f"Cloning repository {repository.full_name} to {target_path}")
            logger.info(f"Clone mode: {'shallow' if shallow else 'full'}, timeout: {timeout}s")
            
            # Configure git environment for the clone
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'  # Disable password prompts
            env['GIT_ASKPASS'] = 'echo'  # Disable credential prompts
            
            # Prepare clone options
            clone_kwargs = {
                'to_path': target_path,
                'env': env,
                'multi_options': [
                    f'--config http.timeout={timeout}',
                    '--config core.compression=0',  # Faster for large repos
                ],
                'allow_unsafe_options': True  # Required for --config options in GitPython
            }
            
            # Add shallow clone options if requested
            if shallow:
                clone_kwargs['depth'] = depth
                clone_kwargs['multi_options'].append('--single-branch')
                logger.info(f"Performing shallow clone with depth={depth}")
            
            # Perform the clone operation
            repo = None
            try:
                repo = git.Repo.clone_from(clone_url, **clone_kwargs)
            except GitCommandError as e:
                # Parse git error for specific issues
                error_msg = str(e).lower()
                
                if 'authentication failed' in error_msg or 'auth' in error_msg:
                    raise CloneAuthenticationError(
                        f"Authentication failed for {repository.full_name}. "
                        "Please check your access token."
                    )
                elif 'timed out' in error_msg or 'timeout' in error_msg:
                    raise CloneTimeoutError(
                        f"Clone operation timed out after {timeout}s for {repository.full_name}"
                    )
                elif 'network' in error_msg or 'connection' in error_msg:
                    raise CloneNetworkError(
                        f"Network error while cloning {repository.full_name}: {error_msg}"
                    )
                else:
                    raise CloneError(f"Git error: {error_msg}")
            
            # Validate the cloned repository
            if not os.path.exists(os.path.join(target_path, '.git')):
                raise CloneError("Clone completed but .git directory not found")
            
            # Calculate repository metadata
            duration = time.time() - start_time
            size_mb = self._calculate_directory_size(target_path)
            commit_count = None
            
            if repo:
                try:
                    # Get commit count (may be limited for shallow clones)
                    commit_count = sum(1 for _ in repo.iter_commits())
                except Exception as e:
                    logger.warning(f"Could not count commits: {e}")
            
            logger.info(
                f"Successfully cloned {repository.full_name} "
                f"({size_mb:.2f} MB, {commit_count or '?'} commits) in {duration:.2f}s"
            )
            
            return CloneResult(
                success=True,
                path=target_path,
                size_mb=size_mb,
                duration_seconds=duration,
                commit_count=commit_count
            )
            
        except (CloneAuthenticationError, CloneTimeoutError, CloneNetworkError) as e:
            # Specific clone errors - already logged
            logger.error(f"Clone failed for {repository.full_name}: {e}")
            
            # Cleanup on failure
            if cleanup_on_failure and os.path.exists(target_path):
                logger.info(f"Cleaning up failed clone at {target_path}")
                shutil.rmtree(target_path, ignore_errors=True)
            
            return CloneResult(
                success=False,
                error=str(e)
            )
            
        except CloneError as e:
            logger.error(f"Clone failed for {repository.full_name}: {e}")
            
            # Cleanup on failure
            if cleanup_on_failure and os.path.exists(target_path):
                logger.info(f"Cleaning up failed clone at {target_path}")
                shutil.rmtree(target_path, ignore_errors=True)
            
            return CloneResult(
                success=False,
                error=str(e)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error cloning {repository.full_name}: {str(e)}", exc_info=True)
            
            # Cleanup on failure
            if cleanup_on_failure and os.path.exists(target_path):
                logger.info(f"Cleaning up failed clone at {target_path}")
                shutil.rmtree(target_path, ignore_errors=True)
            
            return CloneResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _prepare_clone_url(self, repository: Repository) -> str:
        """
        Prepare the clone URL with authentication for private repos.
        
        Args:
            repository: Repository object
            
        Returns:
            Clone URL with authentication if needed
        """
        clone_url = repository.clone_url
        
        # Always use token for authentication (works for both public and private)
        # This ensures consistent behavior and avoids credential prompts
        if self.access_token:
            # Remove any existing authentication from URL
            if '@' in clone_url:
                clone_url = 'https://' + clone_url.split('@')[-1]
            
            # Inject token into URL
            clone_url = clone_url.replace(
                "https://", 
                f"https://oauth2:{self.access_token}@"
            )
        
        return clone_url
    
    def _calculate_directory_size(self, path: str) -> float:
        """
        Calculate the total size of a directory in MB.
        
        Args:
            path: Directory path
            
        Returns:
            Size in megabytes
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"Error calculating directory size: {e}")
        
        return total_size / (1024 * 1024)  # Convert to MB
    
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
