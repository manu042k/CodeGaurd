"""
Repository Analysis Service
Integrates GitHub cloning with multi-agent code analysis
"""

import logging
import tempfile
import shutil
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from ..services.github_service import GitHubService, CloneResult
from ..coordinator import AnalysisCoordinator, AnalysisConfig
from ..models.database import Repository

logger = logging.getLogger(__name__)


class RepositoryAnalysisService:
    """
    Service for cloning and analyzing GitHub repositories
    
    Workflow:
    1. Clone repository from GitHub
    2. Run multi-agent analysis
    3. Clean up cloned files
    4. Return comprehensive report
    """
    
    def __init__(
        self,
        github_service: GitHubService,
        analysis_config: Optional[AnalysisConfig] = None,
    ):
        """
        Initialize the service
        
        Args:
            github_service: GitHub service for cloning
            analysis_config: Configuration for analysis (optional)
        """
        self.github_service = github_service
        self.analysis_config = analysis_config or AnalysisConfig(
            max_concurrent_files=10,
            timeout_per_file=30,
            use_llm=False,
            enabled_agents=["security", "dependency"],
        )
        self.coordinator = AnalysisCoordinator(config=self.analysis_config)
        
    def add_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a progress callback for real-time updates"""
        self.coordinator.add_progress_callback(callback)
        
    async def clone_and_analyze(
        self,
        repository: Repository,
        shallow: bool = True,
        cleanup: bool = True,
    ) -> Dict[str, Any]:
        """
        Clone a repository and run analysis
        
        Args:
            repository: Repository object from database
            shallow: Whether to do shallow clone (faster)
            cleanup: Whether to clean up cloned files after analysis
            
        Returns:
            Complete analysis report with clone metadata
        """
        start_time = time.time()
        clone_result = None
        clone_path = None
        
        try:
            logger.info(f"Starting clone and analysis for {repository.full_name}")
            
            # Step 1: Clone repository
            logger.info(f"Cloning repository {repository.full_name}...")
            clone_start = time.time()
            
            # Create temporary directory for clone
            temp_dir = tempfile.mkdtemp(prefix="codeguard_clone_")
            clone_path = Path(temp_dir) / repository.name
            
            clone_result = self.github_service.clone_repository(
                repository=repository,
                target_path=str(clone_path),
                shallow=shallow,
                depth=1 if shallow else None,
            )
            
            clone_duration = time.time() - clone_start
            
            if not clone_result.success:
                return {
                    "status": "failed",
                    "error": f"Clone failed: {clone_result.error}",
                    "clone_result": self._clone_result_to_dict(clone_result),
                    "duration": time.time() - start_time,
                }
            
            logger.info(
                f"Clone completed in {clone_duration:.2f}s "
                f"({clone_result.size_mb:.2f} MB, {clone_result.commit_count or '?'} commits)"
            )
            
            # Step 2: Analyze repository
            logger.info(f"Starting analysis of {repository.full_name}...")
            analysis_start = time.time()
            
            analysis_report = await self.coordinator.analyze_repository(
                repo_path=str(clone_path)
            )
            
            analysis_duration = time.time() - analysis_start
            logger.info(
                f"Analysis completed in {analysis_duration:.2f}s "
                f"({analysis_report['total_issues']} issues found)"
            )
            
            # Step 3: Build complete report
            total_duration = time.time() - start_time
            
            complete_report = {
                "status": "success",
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "full_name": repository.full_name,
                    "url": repository.html_url,
                    "language": repository.language,
                    "stars": repository.stargazers_count,
                    "forks": repository.forks_count,
                },
                "clone": {
                    "success": True,
                    "duration": clone_duration,
                    "size_mb": clone_result.size_mb,
                    "commit_count": clone_result.commit_count,
                    "shallow": shallow,
                },
                "analysis": analysis_report,
                "timing": {
                    "total_duration": total_duration,
                    "clone_duration": clone_duration,
                    "analysis_duration": analysis_duration,
                },
                "metadata": {
                    "analyzed_at": time.time(),
                    "agents_used": [agent["name"] for agent in self.coordinator.get_agent_info()],
                },
            }
            
            logger.info(
                f"Complete analysis for {repository.full_name}: "
                f"{analysis_report['files_analyzed']} files, "
                f"{analysis_report['total_issues']} issues, "
                f"score: {analysis_report['summary']['overall_score']}/100"
            )
            
            return complete_report
            
        except Exception as e:
            logger.error(f"Error during clone and analysis: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "repository": {
                    "full_name": repository.full_name if repository else "unknown",
                },
                "duration": time.time() - start_time,
            }
            
        finally:
            # Step 4: Cleanup
            if cleanup and clone_path and Path(clone_path).exists():
                try:
                    logger.info(f"Cleaning up cloned repository at {clone_path}")
                    shutil.rmtree(clone_path, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {clone_path}: {e}")
                    
    async def analyze_existing_clone(
        self,
        repository: Repository,
        clone_path: str,
    ) -> Dict[str, Any]:
        """
        Analyze an already cloned repository
        
        Args:
            repository: Repository object from database
            clone_path: Path to the cloned repository
            
        Returns:
            Analysis report
        """
        start_time = time.time()
        
        try:
            logger.info(f"Analyzing existing clone at {clone_path}")
            
            if not Path(clone_path).exists():
                return {
                    "status": "failed",
                    "error": f"Clone path does not exist: {clone_path}",
                }
            
            # Run analysis
            analysis_report = await self.coordinator.analyze_repository(
                repo_path=clone_path
            )
            
            duration = time.time() - start_time
            
            return {
                "status": "success",
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "full_name": repository.full_name,
                },
                "analysis": analysis_report,
                "timing": {
                    "duration": duration,
                },
            }
            
        except Exception as e:
            logger.error(f"Error analyzing existing clone: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time,
            }
            
    def _clone_result_to_dict(self, clone_result: CloneResult) -> Dict[str, Any]:
        """Convert CloneResult to dictionary"""
        return {
            "success": clone_result.success,
            "path": clone_result.path,
            "error": clone_result.error,
            "size_mb": clone_result.size_mb,
            "duration_seconds": clone_result.duration_seconds,
            "commit_count": clone_result.commit_count,
        }
