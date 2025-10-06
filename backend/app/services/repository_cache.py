"""
Repository Cache Manager

Manages cloned repositories on disk, including:
- Caching cloned repos to avoid re-cloning
- Cleaning up old/unused clones
- Managing disk space
- Updating existing clones

This is useful for:
1. Avoiding re-cloning the same repo multiple times
2. Managing disk space by cleaning up old clones
3. Keeping clones up-to-date with remote changes
"""

import os
import shutil
import time
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RepositoryCache:
    """
    Manages a cache of cloned repositories on disk.
    
    Cache structure:
    cache_dir/
        <repo_hash_1>/
            .git/
            ...
        <repo_hash_2>/
            .git/
            ...
        cache_index.json
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize repository cache.
        
        Args:
            cache_dir: Directory to store cached repositories. 
                      If None, uses /tmp/codeguard_cache
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".codeguard", "repo_cache")
        
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Repository cache initialized at: {self.cache_dir}")
    
    def get_cache_key(self, repo_full_name: str) -> str:
        """
        Generate a cache key for a repository.
        
        Args:
            repo_full_name: Full name of repository (e.g., 'owner/repo')
            
        Returns:
            Cache key (hash of repo name)
        """
        return hashlib.sha256(repo_full_name.encode()).hexdigest()[:16]
    
    def get_cached_path(self, repo_full_name: str) -> Optional[str]:
        """
        Get the cached path for a repository if it exists and is valid.
        
        Args:
            repo_full_name: Full name of repository
            
        Returns:
            Path to cached repository, or None if not cached or invalid
        """
        cache_key = self.get_cache_key(repo_full_name)
        cached_path = os.path.join(self.cache_dir, cache_key)
        
        # Check if cache exists and is valid
        if os.path.exists(cached_path):
            git_dir = os.path.join(cached_path, ".git")
            if os.path.exists(git_dir):
                logger.info(f"Found cached repository: {repo_full_name} at {cached_path}")
                return cached_path
            else:
                logger.warning(f"Cached path exists but .git missing: {cached_path}")
                # Clean up invalid cache
                shutil.rmtree(cached_path, ignore_errors=True)
        
        return None
    
    def add_to_cache(self, repo_full_name: str, source_path: str) -> str:
        """
        Add a cloned repository to the cache.
        
        Args:
            repo_full_name: Full name of repository
            source_path: Path to the cloned repository
            
        Returns:
            Path to cached repository
        """
        cache_key = self.get_cache_key(repo_full_name)
        cached_path = os.path.join(self.cache_dir, cache_key)
        
        # Remove existing cache if present
        if os.path.exists(cached_path):
            logger.info(f"Removing existing cache: {cached_path}")
            shutil.rmtree(cached_path, ignore_errors=True)
        
        # Copy to cache
        logger.info(f"Copying {source_path} to cache at {cached_path}")
        shutil.copytree(source_path, cached_path)
        
        # Update access time metadata
        self._update_metadata(cached_path, repo_full_name)
        
        return cached_path
    
    def update_cached_repo(self, repo_full_name: str, github_service) -> bool:
        """
        Update a cached repository by pulling latest changes.
        
        Args:
            repo_full_name: Full name of repository
            github_service: GitHubService instance for authentication
            
        Returns:
            True if update successful, False otherwise
        """
        cached_path = self.get_cached_path(repo_full_name)
        
        if not cached_path:
            logger.warning(f"Cannot update: repository not in cache: {repo_full_name}")
            return False
        
        try:
            import git
            
            repo = git.Repo(cached_path)
            origin = repo.remotes.origin
            
            logger.info(f"Pulling latest changes for {repo_full_name}")
            origin.pull()
            
            # Update metadata
            self._update_metadata(cached_path, repo_full_name)
            
            logger.info(f"Successfully updated cached repository: {repo_full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cached repository {repo_full_name}: {e}")
            return False
    
    def clean_cache(self, max_age_days: int = 7, max_size_gb: Optional[float] = None):
        """
        Clean up old cached repositories.
        
        Args:
            max_age_days: Remove caches older than this many days
            max_size_gb: If total cache size exceeds this, remove oldest first
        """
        logger.info(f"Cleaning cache: max_age={max_age_days} days, max_size={max_size_gb} GB")
        
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        # Get all cached repos with their metadata
        cached_repos = []
        for entry in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(path):
                try:
                    stats = os.stat(path)
                    size_mb = self._get_dir_size(path) / (1024 * 1024)
                    cached_repos.append({
                        'path': path,
                        'name': entry,
                        'atime': stats.st_atime,
                        'size_mb': size_mb
                    })
                except Exception as e:
                    logger.warning(f"Error getting stats for {path}: {e}")
        
        # Sort by access time (oldest first)
        cached_repos.sort(key=lambda x: x['atime'])
        
        # Remove old caches
        removed_count = 0
        total_size_removed = 0
        
        for repo in cached_repos:
            should_remove = False
            
            # Check age
            if repo['atime'] < cutoff_time:
                logger.info(f"Removing old cache: {repo['name']} (age: {(time.time() - repo['atime']) / 86400:.1f} days)")
                should_remove = True
            
            # Check total size if specified
            if max_size_gb:
                total_size = sum(r['size_mb'] for r in cached_repos) / 1024
                if total_size > max_size_gb and repo['atime'] < time.time():
                    logger.info(f"Removing cache to free space: {repo['name']} ({repo['size_mb']:.1f} MB)")
                    should_remove = True
            
            if should_remove:
                try:
                    shutil.rmtree(repo['path'], ignore_errors=True)
                    removed_count += 1
                    total_size_removed += repo['size_mb']
                except Exception as e:
                    logger.error(f"Error removing cache {repo['path']}: {e}")
        
        logger.info(f"Cache cleanup complete: removed {removed_count} repos ({total_size_removed:.1f} MB)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        total_size = 0
        repo_count = 0
        oldest_time = None
        newest_time = None
        
        for entry in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(path):
                try:
                    stats = os.stat(path)
                    size = self._get_dir_size(path)
                    total_size += size
                    repo_count += 1
                    
                    if oldest_time is None or stats.st_atime < oldest_time:
                        oldest_time = stats.st_atime
                    if newest_time is None or stats.st_atime > newest_time:
                        newest_time = stats.st_atime
                except Exception:
                    pass
        
        return {
            'cache_dir': self.cache_dir,
            'repo_count': repo_count,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'oldest_access': datetime.fromtimestamp(oldest_time).isoformat() if oldest_time else None,
            'newest_access': datetime.fromtimestamp(newest_time).isoformat() if newest_time else None
        }
    
    def _get_dir_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"Error calculating directory size for {path}: {e}")
        return total
    
    def _update_metadata(self, cached_path: str, repo_full_name: str):
        """Update metadata file for cached repository"""
        try:
            metadata_file = os.path.join(cached_path, ".codeguard_cache_metadata")
            with open(metadata_file, 'w') as f:
                f.write(f"repo_name={repo_full_name}\n")
                f.write(f"cached_at={datetime.utcnow().isoformat()}\n")
                f.write(f"last_accessed={datetime.utcnow().isoformat()}\n")
        except Exception as e:
            logger.warning(f"Could not write metadata: {e}")


def example_usage():
    """Example usage of RepositoryCache"""
    cache = RepositoryCache()
    
    # Get cache stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Clean old caches
    cache.clean_cache(max_age_days=7, max_size_gb=5.0)
    
    # Check if repo is cached
    cached_path = cache.get_cached_path("octocat/Hello-World")
    if cached_path:
        print(f"Repository is cached at: {cached_path}")
    else:
        print("Repository not in cache")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
