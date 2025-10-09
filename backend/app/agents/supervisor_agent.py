"""
Supervisor Agent - Orchestrates all other agents and manages the analysis pipeline
"""
import os
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from .base_agent import BaseAgent
from .code_quality_agent import CodeQualityAgent
from .security_agent import SecurityAgent
from .architecture_agent import ArchitectureAgent
from .documentation_agent import DocumentationAgent
from .testing_agent import TestingAgent
from .dependency_agent import DependencyAgent
from .static_tool_agent import StaticToolAgent
from .summary_agent import SummaryAgent

class SupervisorAgent(BaseAgent):
    """Master agent that orchestrates all other analysis agents"""
    
    def __init__(self, llm_provider):
        super().__init__("Supervisor Agent", "Orchestration", llm_provider)
        
        # Initialize all analysis agents
        self.agents = {
            'code_quality': CodeQualityAgent(llm_provider),
            'security': SecurityAgent(llm_provider),
            'architecture': ArchitectureAgent(llm_provider),
            'documentation': DocumentationAgent(llm_provider),
            'testing': TestingAgent(llm_provider),
            'dependency': DependencyAgent(llm_provider),
            'static_tool': StaticToolAgent(llm_provider)
        }
        
        self.summary_agent = SummaryAgent(llm_provider)
        
        # Configuration
        self.max_concurrent_agents = 3  # Limit concurrent execution
        self.agent_timeout = 300  # 5 minutes per agent
        self.retry_attempts = 2
    
    async def run_full_analysis(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run complete analysis pipeline with all agents"""
        analysis_start_time = time.time()
        self.logger.info(f"Starting full analysis pipeline for {repo_path}")
        
        # Validate repository
        validation_result = self._validate_repository(repo_path)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Prepare analysis context
        analysis_context = self._prepare_analysis_context(repo_path, context)
        
        # Run agents with orchestration
        agent_results = await self._orchestrate_agents(repo_path, analysis_context)
        
        # Generate summary and aggregated results
        aggregated_results = self.summary_agent.aggregate_results(agent_results, repo_path, analysis_context)
        
        # Add LLM-generated insights
        llm_summary = await self.summary_agent.generate_llm_summary(aggregated_results, repo_path)
        aggregated_results.update(llm_summary)
        
        # Calculate execution metrics
        total_execution_time = time.time() - analysis_start_time
        
        # Final result structure
        final_result = {
            'success': True,
            'repo_path': repo_path,
            'execution_time': round(total_execution_time, 2),
            'agents_executed': list(agent_results.keys()),
            'failed_agents': [name for name, result in agent_results.items() if result.get('error')],
            'analysis_metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'supervisor_version': '1.0',
                'total_agents': len(self.agents),
                'successful_agents': len([r for r in agent_results.values() if not r.get('error')]),
                'repository_stats': analysis_context.get('repository_stats', {})
            },
            **aggregated_results
        }
        
        self.logger.info(f"Analysis completed in {total_execution_time:.2f} seconds")
        return final_result
    
    def _validate_repository(self, repo_path: str) -> Dict[str, Any]:
        """Validate that the repository path exists and is analyzable"""
        if not os.path.exists(repo_path):
            return {'valid': False, 'error': f'Repository path does not exist: {repo_path}'}
        
        if not os.path.isdir(repo_path):
            return {'valid': False, 'error': f'Path is not a directory: {repo_path}'}
        
        # Check if directory has any files
        has_files = False
        for root, dirs, files in os.walk(repo_path):
            if files:
                has_files = True
                break
        
        if not has_files:
            return {'valid': False, 'error': 'Repository directory is empty'}
        
        return {'valid': True}
    
    def _prepare_analysis_context(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Prepare analysis context with repository information"""
        analysis_context = context.copy() if context else {}
        
        # Get repository statistics
        repo_stats = self._get_repository_stats(repo_path)
        analysis_context['repository_stats'] = repo_stats
        
        # Detect primary languages
        languages = self._detect_primary_languages(repo_path)
        analysis_context['primary_languages'] = languages
        
        # Check for special files/configurations
        special_files = self._detect_special_files(repo_path)
        analysis_context['special_files'] = special_files
        
        # Set analysis preferences based on repository characteristics
        analysis_context['analysis_preferences'] = self._determine_analysis_preferences(
            repo_stats, languages, special_files
        )
        
        return analysis_context
    
    def _get_repository_stats(self, repo_path: str) -> Dict[str, Any]:
        """Get basic repository statistics"""
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'file_extensions': {},
            'directory_count': 0,
            'max_depth': 0
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Calculate depth
                depth = root.replace(repo_path, '').count(os.sep)
                stats['max_depth'] = max(stats['max_depth'], depth)
                stats['directory_count'] += len(dirs)
                
                for file in files:
                    if not file.startswith('.'):  # Skip hidden files
                        stats['total_files'] += 1
                        
                        try:
                            file_path = os.path.join(root, file)
                            stats['total_size_bytes'] += os.path.getsize(file_path)
                            
                            # Track extensions
                            ext = os.path.splitext(file)[1].lower()
                            if ext:
                                stats['file_extensions'][ext] = stats['file_extensions'].get(ext, 0) + 1
                        except OSError:
                            continue
        
        except Exception as e:
            self.logger.error(f"Error getting repository stats: {e}")
        
        return stats
    
    def _detect_primary_languages(self, repo_path: str) -> List[str]:
        """Detect primary programming languages in the repository"""
        language_mappings = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        extension_counts = {}
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build']]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in language_mappings:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Determine primary languages (must have at least 3 files)
        primary_languages = []
        for ext, count in extension_counts.items():
            if count >= 3:
                primary_languages.append(language_mappings[ext])
        
        # Sort by file count
        primary_languages.sort(key=lambda lang: sum(
            count for ext, count in extension_counts.items() 
            if language_mappings.get(ext) == lang
        ), reverse=True)
        
        return primary_languages
    
    def _detect_special_files(self, repo_path: str) -> Dict[str, List[str]]:
        """Detect special configuration and project files"""
        special_files = {
            'dependency_files': [],
            'config_files': [],
            'documentation_files': [],
            'ci_files': [],
            'container_files': []
        }
        
        # File patterns to look for
        patterns = {
            'dependency_files': [
                'requirements.txt', 'package.json', 'pom.xml', 'build.gradle', 
                'Gemfile', 'composer.json', 'go.mod', 'Cargo.toml', 'pyproject.toml'
            ],
            'config_files': [
                '.env', 'config.json', 'settings.json', '.gitignore', 
                'tsconfig.json', 'webpack.config.js', 'babel.config.js'
            ],
            'documentation_files': [
                'README.md', 'README.rst', 'CHANGELOG.md', 'CONTRIBUTING.md', 
                'LICENSE', 'docs/', 'documentation/'
            ],
            'ci_files': [
                '.github/', '.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml', 
                'azure-pipelines.yml', '.circleci/'
            ],
            'container_files': [
                'Dockerfile', 'docker-compose.yml', '.dockerignore', 'kubernetes/'
            ]
        }
        
        for root, dirs, files in os.walk(repo_path):
            rel_root = os.path.relpath(root, repo_path)
            
            for category, file_patterns in patterns.items():
                for pattern in file_patterns:
                    if pattern.endswith('/'):
                        # Directory pattern
                        if pattern.rstrip('/') in dirs:
                            special_files[category].append(os.path.join(rel_root, pattern.rstrip('/')))
                    else:
                        # File pattern
                        if pattern in files:
                            special_files[category].append(os.path.join(rel_root, pattern))
        
        return special_files
    
    def _determine_analysis_preferences(self, repo_stats: Dict[str, Any], 
                                      languages: List[str], special_files: Dict[str, List[str]]) -> Dict[str, Any]:
        """Determine analysis preferences based on repository characteristics"""
        preferences = {
            'prioritize_security': False,
            'focus_on_testing': False,
            'emphasize_documentation': False,
            'check_dependencies': False,
            'run_static_analysis': False
        }
        
        # Security priority for web applications or if security-sensitive languages
        if any(lang in ['JavaScript', 'TypeScript', 'PHP', 'Python'] for lang in languages):
            preferences['prioritize_security'] = True
        
        # Testing focus for larger codebases
        if repo_stats['total_files'] > 50:
            preferences['focus_on_testing'] = True
        
        # Documentation emphasis for open-source projects or libraries
        if any('README' in file for file in special_files.get('documentation_files', [])):
            preferences['emphasize_documentation'] = True
        
        # Dependency checking if dependency files present
        if special_files.get('dependency_files'):
            preferences['check_dependencies'] = True
        
        # Static analysis for supported languages
        supported_static_languages = ['Python', 'JavaScript', 'TypeScript', 'Java']
        if any(lang in supported_static_languages for lang in languages):
            preferences['run_static_analysis'] = True
        
        return preferences
    
    async def _orchestrate_agents(self, repo_path: str, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Orchestrate the execution of all analysis agents"""
        agent_results = {}
        
        # Determine agent execution order based on preferences
        execution_plan = self._create_execution_plan(context.get('analysis_preferences', {}))
        
        # Execute agents in batches to control concurrency
        for batch in execution_plan:
            batch_tasks = []
            
            for agent_name in batch:
                if agent_name in self.agents:
                    task = self._run_agent_with_retry(agent_name, repo_path, context)
                    batch_tasks.append((agent_name, task))
            
            # Execute batch
            if batch_tasks:
                self.logger.info(f"Executing batch: {[name for name, _ in batch_tasks]}")
                batch_results = await asyncio.gather(
                    *[task for _, task in batch_tasks],
                    return_exceptions=True
                )
                
                # Process batch results
                for (agent_name, _), result in zip(batch_tasks, batch_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Agent {agent_name} failed with exception: {result}")
                        agent_results[agent_name] = {
                            'error': str(result),
                            'agent': agent_name,
                            'category': self.agents[agent_name].category,
                            'score': 0,
                            'issues': [],
                            'suggestions': [],
                            'summary': f"Agent failed: {str(result)}"
                        }
                    else:
                        agent_results[agent_name] = result
        
        return agent_results
    
    def _create_execution_plan(self, preferences: Dict[str, Any]) -> List[List[str]]:
        """Create agent execution plan based on preferences and dependencies"""
        
        # Define execution batches (agents that can run concurrently)
        if preferences.get('prioritize_security', False):
            # Security-first approach
            execution_plan = [
                ['security'],  # Security first
                ['code_quality', 'static_tool'],  # Code quality checks
                ['architecture', 'dependency'],  # Structural analysis
                ['testing', 'documentation']  # Supporting analyses
            ]
        else:
            # Balanced approach
            execution_plan = [
                ['code_quality', 'security'],  # Core quality and security
                ['architecture', 'static_tool'],  # Structural and static analysis
                ['testing', 'dependency'],  # Testing and dependencies
                ['documentation']  # Documentation last
            ]
        
        # Filter out agents based on preferences
        if not preferences.get('run_static_analysis', True):
            for batch in execution_plan:
                if 'static_tool' in batch:
                    batch.remove('static_tool')
        
        if not preferences.get('check_dependencies', True):
            for batch in execution_plan:
                if 'dependency' in batch:
                    batch.remove('dependency')
        
        # Remove empty batches
        execution_plan = [batch for batch in execution_plan if batch]
        
        return execution_plan
    
    async def _run_agent_with_retry(self, agent_name: str, repo_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run an agent with retry logic and error handling"""
        agent = self.agents[agent_name]
        
        for attempt in range(self.retry_attempts + 1):
            try:
                self.logger.info(f"Running {agent_name} (attempt {attempt + 1})")
                
                # Run agent with timeout
                result = await asyncio.wait_for(
                    agent.analyze(repo_path, context),
                    timeout=self.agent_timeout
                )
                
                # Validate result
                if self._validate_agent_result(result):
                    self.logger.info(f"{agent_name} completed successfully")
                    return result
                else:
                    raise ValueError(f"Invalid result from {agent_name}")
            
            except asyncio.TimeoutError:
                self.logger.error(f"{agent_name} timed out after {self.agent_timeout} seconds")
                if attempt == self.retry_attempts:
                    return self._create_fallback_result(agent_name, "Agent timed out")
            
            except Exception as e:
                self.logger.error(f"{agent_name} failed on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts:
                    return self._create_fallback_result(agent_name, str(e))
                
                # Wait before retry
                await asyncio.sleep(2)
        
        return self._create_fallback_result(agent_name, "Max retry attempts exceeded")
    
    def _validate_agent_result(self, result: Dict[str, Any]) -> bool:
        """Validate that an agent result has the required structure"""
        required_fields = ['agent', 'category', 'score', 'issues', 'suggestions', 'summary']
        
        if not isinstance(result, dict):
            return False
        
        for field in required_fields:
            if field not in result:
                return False
        
        # Validate field types
        if not isinstance(result['score'], (int, float)) or not (0 <= result['score'] <= 100):
            return False
        
        if not isinstance(result['issues'], list):
            return False
        
        if not isinstance(result['suggestions'], list):
            return False
        
        return True
    
    def _create_fallback_result(self, agent_name: str, error_message: str) -> Dict[str, Any]:
        """Create a fallback result when an agent fails"""
        agent = self.agents[agent_name]
        
        return {
            'agent': agent_name,
            'category': agent.category,
            'score': 0,
            'issues': [{
                'desc': f"Agent analysis failed: {error_message}",
                'severity': 'high'
            }],
            'suggestions': ['Investigate agent failure and retry analysis'],
            'summary': f"Analysis failed for {agent.category}: {error_message}",
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def run_selective_analysis(self, repo_path: str, agent_names: List[str], 
                                   context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run analysis with only selected agents"""
        self.logger.info(f"Running selective analysis with agents: {agent_names}")
        
        # Validate repository
        validation_result = self._validate_repository(repo_path)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Filter agents
        selected_agents = {name: agent for name, agent in self.agents.items() if name in agent_names}
        
        if not selected_agents:
            return {
                'success': False,
                'error': 'No valid agents selected',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Prepare context
        analysis_context = self._prepare_analysis_context(repo_path, context)
        
        # Run selected agents
        agent_results = {}
        tasks = []
        
        for agent_name, agent in selected_agents.items():
            task = self._run_agent_with_retry(agent_name, repo_path, analysis_context)
            tasks.append((agent_name, task))
        
        # Execute all selected agents
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (agent_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                agent_results[agent_name] = self._create_fallback_result(agent_name, str(result))
            else:
                agent_results[agent_name] = result
        
        # Generate summary
        aggregated_results = self.summary_agent.aggregate_results(agent_results, repo_path, analysis_context)
        
        return {
            'success': True,
            'repo_path': repo_path,
            'agents_executed': list(agent_results.keys()),
            'failed_agents': [name for name, result in agent_results.items() if result.get('error')],
            **aggregated_results
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about all agents"""
        return {
            'supervisor_version': '1.0',
            'total_agents': len(self.agents),
            'available_agents': list(self.agents.keys()),
            'agent_details': {
                name: {
                    'name': agent.name,
                    'category': agent.category
                }
                for name, agent in self.agents.items()
            },
            'configuration': {
                'max_concurrent_agents': self.max_concurrent_agents,
                'agent_timeout': self.agent_timeout,
                'retry_attempts': self.retry_attempts
            }
        }
    
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Implement the abstract analyze method from BaseAgent
        This serves as the main entry point for the supervisor
        """
        return await self.run_full_analysis(repo_path, context)
