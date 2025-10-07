"""
Analysis Coordinator
Orchestrates parallel execution of multiple agents across repository files
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Set
from pathlib import Path
import logging

from ..agents.base_agent import BaseAgent, AgentResult
from ..agents import (
    SecurityAgent,
    DependencyAgent,
    CodeQualityAgent,
    PerformanceAgent,
    BestPracticesAgent
)
from ..parsers.language_detector import LanguageDetector
from ..utils.file_scanner import FileScanner
from .result_aggregator import ResultAggregator

logger = logging.getLogger(__name__)


class AnalysisConfig:
    """Configuration for analysis execution"""
    
    def __init__(
        self,
        max_concurrent_files: int = 10,
        timeout_per_file: int = 30,
        use_llm: bool = False,
        enabled_agents: Optional[List[str]] = None,
        skip_patterns: Optional[List[str]] = None,
    ):
        self.max_concurrent_files = max_concurrent_files
        self.timeout_per_file = timeout_per_file
        self.use_llm = use_llm
        self.enabled_agents = enabled_agents or [
            "security",
            "dependency",
            "code_quality",
            "performance",
            "best_practices"
        ]
        self.skip_patterns = skip_patterns or [
            "*.min.js",
            "*.map",
            "node_modules/*",
            "__pycache__/*",
            ".git/*",
            "*.pyc",
            "venv/*",
            "env/*",
            ".venv/*",
            "dist/*",
            "build/*",
        ]


class AnalysisProgress:
    """Track analysis progress"""
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.completed_files = 0
        self.failed_files = 0
        self.total_issues = 0
        self.agent_stats: Dict[str, Dict[str, int]] = {}
        self.start_time = time.time()
        
    def update(self, agent_name: str, success: bool, issues_count: int = 0):
        """Update progress"""
        if success:
            self.completed_files += 1
            self.total_issues += issues_count
        else:
            self.failed_files += 1
            
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {"runs": 0, "issues": 0}
        
        self.agent_stats[agent_name]["runs"] += 1
        self.agent_stats[agent_name]["issues"] += issues_count
        
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
        
    @property
    def progress_percent(self) -> float:
        """Get progress percentage"""
        total_processed = self.completed_files + self.failed_files
        if self.total_files == 0:
            return 100.0
        return (total_processed / self.total_files) * 100
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_files": self.total_files,
            "completed_files": self.completed_files,
            "failed_files": self.failed_files,
            "total_issues": self.total_issues,
            "progress_percent": round(self.progress_percent, 2),
            "elapsed_time": round(self.elapsed_time, 2),
            "agent_stats": self.agent_stats,
        }


class AnalysisCoordinator:
    """
    Coordinates multi-agent analysis across repository files
    
    Features:
    - Parallel agent execution with asyncio
    - Progress tracking and callbacks
    - Error handling and retry logic
    - Resource management
    - Result aggregation
    """
    
    def __init__(
        self,
        config: Optional[AnalysisConfig] = None,
        agents: Optional[List[BaseAgent]] = None,
    ):
        """
        Initialize coordinator
        
        Args:
            config: Analysis configuration
            agents: List of agents to use (if None, creates default agents)
        """
        self.config = config or AnalysisConfig()
        
        # Initialize agents
        if agents is None:
            self.agents = self._create_default_agents()
        else:
            self.agents = agents
            
        # Filter agents based on enabled list
        self.agents = [
            agent for agent in self.agents
            if agent.name.replace("Agent", "").lower() in [
                name.lower() for name in self.config.enabled_agents
            ]
        ]
        
        # Initialize utilities
        self.language_detector = LanguageDetector()
        self.file_scanner = FileScanner()
        self.result_aggregator = ResultAggregator()
        
        # Progress tracking
        self.progress: Optional[AnalysisProgress] = None
        self.progress_callbacks: List[Callable] = []
        
    def _create_default_agents(self) -> List[BaseAgent]:
        """Create default set of agents"""
        agent_config = {"use_llm": self.config.use_llm}
        
        agents = []
        
        # Add agents that are confirmed working
        try:
            agents.append(SecurityAgent(agent_config))
        except Exception as e:
            logger.warning(f"Failed to initialize SecurityAgent: {e}")
            
        try:
            agents.append(DependencyAgent(agent_config))
        except Exception as e:
            logger.warning(f"Failed to initialize DependencyAgent: {e}")
        
        # Try to add other agents if they're available
        try:
            agents.append(CodeQualityAgent(agent_config))
        except Exception as e:
            logger.warning(f"Failed to initialize CodeQualityAgent: {e}")
            
        try:
            agents.append(PerformanceAgent(agent_config))
        except Exception as e:
            logger.warning(f"Failed to initialize PerformanceAgent: {e}")
            
        try:
            agents.append(BestPracticesAgent(agent_config))
        except Exception as e:
            logger.warning(f"Failed to initialize BestPracticesAgent: {e}")
        
        if not agents:
            raise RuntimeError("No agents could be initialized")
            
        return agents
        
    def add_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback for progress updates"""
        self.progress_callbacks.append(callback)
        
    def _notify_progress(self):
        """Notify all progress callbacks"""
        if self.progress:
            progress_data = self.progress.to_dict()
            for callback in self.progress_callbacks:
                try:
                    callback(progress_data)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
                    
    async def analyze_repository(
        self,
        repo_path: str,
        include_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze entire repository
        
        Args:
            repo_path: Path to repository root
            include_patterns: File patterns to include (e.g., ["*.py", "*.js"])
            
        Returns:
            Aggregated analysis report
        """
        logger.info(f"Starting repository analysis: {repo_path}")
        start_time = time.time()
        
        # Step 1: Scan files
        logger.info("Scanning repository files...")
        all_files = self.file_scanner.scan_directory(repo_path)
        
        # Filter files based on include/exclude patterns (if needed)
        # For now, we get relative paths from FileInfo objects
        files = [f.relative_path for f in all_files if not f.is_binary]
        
        logger.info(f"Found {len(files)} files to analyze")
        
        if not files:
            return {
                "status": "completed",
                "repository": repo_path,
                "files_analyzed": 0,
                "total_issues": 0,
                "issues": [],
                "summary": {"message": "No files found to analyze"},
                "duration": 0,
            }
        
        # Step 2: Initialize progress tracking
        self.progress = AnalysisProgress(len(files))
        self._notify_progress()
        
        # Step 3: Analyze files in parallel
        logger.info("Starting parallel analysis...")
        results = await self._analyze_files_parallel(repo_path, files)
        
        # Step 4: Aggregate results
        logger.info("Aggregating results...")
        aggregated_report = self.result_aggregator.aggregate(
            results=results,
            repository_path=repo_path,
        )
        
        # Step 5: Add metadata
        duration = time.time() - start_time
        aggregated_report["duration"] = round(duration, 2)
        aggregated_report["progress"] = self.progress.to_dict()
        
        logger.info(
            f"Analysis completed in {duration:.2f}s: "
            f"{aggregated_report['summary']['total_issues']} issues found"
        )
        
        return aggregated_report
        
    async def _analyze_files_parallel(
        self,
        repo_path: str,
        files: List[str],
    ) -> List[AgentResult]:
        """
        Analyze files in parallel with rate limiting
        
        Args:
            repo_path: Repository root path
            files: List of file paths
            
        Returns:
            List of agent results
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent_files)
        
        async def analyze_file_with_limit(file_path: str) -> List[AgentResult]:
            async with semaphore:
                return await self._analyze_single_file(repo_path, file_path)
        
        # Create tasks for all files
        tasks = [analyze_file_with_limit(file_path) for file_path in files]
        
        # Execute with progress tracking
        all_results = []
        for coro in asyncio.as_completed(tasks):
            try:
                file_results = await coro
                all_results.extend(file_results)
            except Exception as e:
                logger.error(f"File analysis failed: {e}")
                
            self._notify_progress()
        
        return all_results
        
    async def _analyze_single_file(
        self,
        repo_path: str,
        file_path: str,
    ) -> List[AgentResult]:
        """
        Analyze single file with all applicable agents
        
        Args:
            repo_path: Repository root path
            file_path: File path relative to repo root
            
        Returns:
            List of agent results
        """
        full_path = Path(repo_path) / file_path
        
        try:
            # Read file content
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            # Detect language
            language = self.language_detector.detect_language(str(full_path))
            
            # Find applicable agents
            applicable_agents = [
                agent for agent in self.agents
                if language in agent.supported_languages
            ]
            
            if not applicable_agents:
                logger.debug(f"No agents support language '{language}' for {file_path}")
                return []
            
            # Run agents in parallel for this file
            agent_tasks = [
                self._run_agent_with_timeout(
                    agent, str(file_path), content, language
                )
                for agent in applicable_agents
            ]
            
            results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Agent error for {file_path}: {result}")
                    continue
                if result is not None:
                    valid_results.append(result)
                    self.progress.update(
                        result.agent_name,
                        success=True,
                        issues_count=len(result.issues)
                    )
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            if self.progress:
                self.progress.update("unknown", success=False)
            return []
            
    async def _run_agent_with_timeout(
        self,
        agent: BaseAgent,
        file_path: str,
        content: str,
        language: str,
    ) -> Optional[AgentResult]:
        """
        Run agent with timeout protection
        
        Args:
            agent: Agent to run
            file_path: File path
            content: File content
            language: Detected language
            
        Returns:
            Agent result or None if timeout
        """
        try:
            result = await asyncio.wait_for(
                agent.analyze(
                    file_path=file_path,
                    file_content=content,
                    language=language,
                ),
                timeout=self.config.timeout_per_file,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout: {agent.name} analysis of {file_path} "
                f"exceeded {self.config.timeout_per_file}s"
            )
            return None
        except Exception as e:
            logger.error(f"Agent {agent.name} failed on {file_path}: {e}")
            return None
            
    async def analyze_files(
        self,
        files: List[Dict[str, str]],
        repo_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze specific list of files (with content provided)
        
        Args:
            files: List of dicts with 'path', 'content', and optionally 'language'
            repo_path: Optional repository path for context
            
        Returns:
            Aggregated analysis report
        """
        logger.info(f"Starting analysis of {len(files)} provided files")
        start_time = time.time()
        
        # Initialize progress
        self.progress = AnalysisProgress(len(files))
        self._notify_progress()
        
        # Analyze files
        all_results = []
        for file_info in files:
            file_path = file_info["path"]
            content = file_info["content"]
            language = file_info.get("language")
            
            if not language:
                language = self.language_detector.detect_language(file_path)
            
            # Find applicable agents
            applicable_agents = [
                agent for agent in self.agents
                if language in agent.supported_languages
            ]
            
            # Run agents
            for agent in applicable_agents:
                try:
                    result = await agent.analyze(
                        file_path=file_path,
                        file_content=content,
                        language=language,
                    )
                    if result:
                        all_results.append(result)
                        self.progress.update(
                            agent.name,
                            success=True,
                            issues_count=len(result.issues)
                        )
                except Exception as e:
                    logger.error(f"Agent {agent.name} failed on {file_path}: {e}")
                    self.progress.update(agent.name, success=False)
            
            self._notify_progress()
        
        # Aggregate results
        aggregated_report = self.result_aggregator.aggregate(
            results=all_results,
            repository_path=repo_path or "provided_files",
        )
        
        duration = time.time() - start_time
        aggregated_report["duration"] = round(duration, 2)
        aggregated_report["progress"] = self.progress.to_dict()
        
        return aggregated_report
        
    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all loaded agents"""
        return [
            {
                "name": agent.name,
                "version": agent.version,
                "description": agent.description,
                "supported_languages": agent.supported_languages,
            }
            for agent in self.agents
        ]
