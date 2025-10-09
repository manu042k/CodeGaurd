"""
Base Agent class for the LLM Static Analysis Platform
"""
import os
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all analysis agents"""
    
    def __init__(self, name: str, category: str, llm_provider):
        self.name = name
        self.category = category
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(f"agent.{name.lower()}")
    
    @abstractmethod
    async def analyze(self, repo_path: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze the repository and return results"""
        pass
    
    def get_file_content(self, file_path: str, max_size: int = 50000) -> Optional[str]:
        """Safely read file content with size limit"""
        try:
            if not os.path.exists(file_path):
                return None
            
            # Check file size
            if os.path.getsize(file_path) > max_size:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_size)
                    return content + "\n... [FILE TRUNCATED DUE TO SIZE]"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def find_files_by_extension(self, repo_path: str, extensions: List[str], 
                               exclude_dirs: Optional[List[str]] = None) -> List[str]:
        """Find files with specific extensions, excluding certain directories"""
        if exclude_dirs is None:
            exclude_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                           'dist', 'build', '.next', 'coverage', '.pytest_cache']
        
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
        
        return files
    
    def get_repo_stats(self, repo_path: str) -> Dict[str, Any]:
        """Get basic repository statistics"""
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'file_types': {},
            'size_bytes': 0
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    try:
                        stats['total_files'] += 1
                        stats['size_bytes'] += os.path.getsize(file_path)
                        
                        # File extension
                        ext = Path(file).suffix.lower()
                        if ext:
                            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                        
                        # Count lines for text files
                        if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go']:
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    stats['total_lines'] += sum(1 for _ in f)
                            except:
                                pass
                                
                    except OSError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error getting repo stats: {e}")
        
        return stats
    
    def create_result_structure(self, score: int, issues: List[Dict] = None, 
                              summary: str = "", suggestions: List[str] = None) -> Dict[str, Any]:
        """Create standardized result structure"""
        return {
            'agent': self.name,
            'category': self.category,
            'score': min(100, max(0, score)),  # Ensure score is 0-100
            'summary': summary,
            'issues': issues or [],
            'suggestions': suggestions or [],
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    
    async def run_with_timeout(self, coro, timeout: int = 300):
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {self.name} timed out after {timeout} seconds")
            return self.create_result_structure(
                score=0,
                summary=f"Analysis timed out after {timeout} seconds",
                issues=[{"desc": "Analysis timeout", "severity": "high"}]
            )
    
    def is_text_file(self, file_path: str) -> bool:
        """Check if file is a text file that can be analyzed"""
        text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.scala',
            '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.txt',
            '.md', '.rst', '.sql', '.sh', '.bash', '.zsh', '.fish',
            '.dockerfile', '.gitignore', '.env'
        }
        
        return Path(file_path).suffix.lower() in text_extensions or Path(file_path).name.lower() in [
            'dockerfile', 'makefile', 'readme', 'license', 'changelog', 'requirements.txt'
        ]
