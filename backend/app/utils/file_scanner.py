"""
File Scanner Utility
Recursively scans directories and identifies files for analysis.
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass
import fnmatch


@dataclass
class FileInfo:
    """Information about a scanned file"""
    path: str
    relative_path: str
    size: int
    extension: str
    name: str
    is_binary: bool = False
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "relative_path": self.relative_path,
            "size": self.size,
            "extension": self.extension,
            "name": self.name,
            "is_binary": self.is_binary,
            "language": self.language,
        }


class FileScanner:
    """Scans directories for code files"""

    # Default patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = [
        # Dependencies
        "node_modules/**",
        "venv/**",
        "env/**",
        ".env/**",
        "virtualenv/**",
        "__pycache__/**",
        "*.pyc",
        ".pytest_cache/**",
        
        # Build outputs
        "build/**",
        "dist/**",
        "target/**",
        "out/**",
        "bin/**",
        "obj/**",
        
        # IDE and editor files
        ".vscode/**",
        ".idea/**",
        "*.swp",
        "*.swo",
        "*~",
        
        # Version control
        ".git/**",
        ".svn/**",
        ".hg/**",
        
        # Package managers
        "vendor/**",
        "bower_components/**",
        
        # Compiled files
        "*.class",
        "*.dll",
        "*.exe",
        "*.o",
        "*.so",
        "*.dylib",
        
        # Archives
        "*.zip",
        "*.tar",
        "*.gz",
        "*.rar",
        
        # Media files
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.ico",
        "*.svg",
        "*.mp4",
        "*.mp3",
        "*.wav",
        
        # Documents
        "*.pdf",
        "*.doc",
        "*.docx",
        
        # Lock files
        "package-lock.json",
        "yarn.lock",
        "poetry.lock",
        "Pipfile.lock",
        
        # Database files
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        
        # Logs
        "*.log",
        "logs/**",
        
        # Temporary files
        "tmp/**",
        "temp/**",
        ".tmp/**",
        
        # OS files
        ".DS_Store",
        "Thumbs.db",
    ]

    # Code file extensions to include
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
        ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".php", ".rb",
        ".swift", ".kt", ".kts", ".scala", ".r", ".m", ".mm",
        ".sql", ".sh", ".bash", ".zsh", ".ps1", ".vue", ".dart",
        ".lua", ".perl", ".pl", ".hs", ".ex", ".exs", ".clj",
        ".elm", ".erl", ".fs", ".fsx", ".ml", ".nim", ".zig",
    }

    # Binary file extensions to always skip
    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
        ".mp3", ".mp4", ".avi", ".mov", ".wav",
        ".zip", ".tar", ".gz", ".rar", ".7z",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".db", ".sqlite", ".sqlite3",
    }

    def __init__(
        self,
        exclude_patterns: Optional[List[str]] = None,
        include_extensions: Optional[Set[str]] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    ):
        """
        Initialize the file scanner
        
        Args:
            exclude_patterns: Patterns to exclude (uses glob syntax)
            include_extensions: File extensions to include
            max_file_size: Maximum file size in bytes
        """
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE_PATTERNS
        self.include_extensions = include_extensions or self.CODE_EXTENSIONS
        self.max_file_size = max_file_size

    def scan_directory(self, directory: str) -> List[FileInfo]:
        """
        Scan a directory recursively for code files
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            List of FileInfo objects
        """
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise ValueError(f"Not a directory: {directory}")

        files: List[FileInfo] = []
        
        for root, dirs, filenames in os.walk(directory):
            # Filter directories in-place to skip excluded patterns
            dirs[:] = [d for d in dirs if not self._should_exclude(
                os.path.join(root, d), directory
            )]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Skip if excluded
                if self._should_exclude(file_path, directory):
                    continue

                # Get file info
                file_info = self._get_file_info(file_path, directory)
                
                if file_info and self._should_include(file_info):
                    files.append(file_info)

        return files

    def scan_files(self, file_paths: List[str], base_dir: Optional[str] = None) -> List[FileInfo]:
        """
        Scan specific files
        
        Args:
            file_paths: List of file paths to scan
            base_dir: Base directory for relative paths
            
        Returns:
            List of FileInfo objects
        """
        files: List[FileInfo] = []
        base_dir = base_dir or os.getcwd()

        for file_path in file_paths:
            if not os.path.isfile(file_path):
                continue

            if self._should_exclude(file_path, base_dir):
                continue

            file_info = self._get_file_info(file_path, base_dir)
            if file_info and self._should_include(file_info):
                files.append(file_info)

        return files

    def _get_file_info(self, file_path: str, base_dir: str) -> Optional[FileInfo]:
        """Get information about a file"""
        try:
            stat = os.stat(file_path)
            
            # Skip if too large
            if stat.st_size > self.max_file_size:
                return None

            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            
            # Check if binary
            is_binary = extension in self.BINARY_EXTENSIONS or self._is_binary_file(file_path)

            relative_path = os.path.relpath(file_path, base_dir)

            return FileInfo(
                path=file_path,
                relative_path=relative_path,
                size=stat.st_size,
                extension=extension,
                name=path_obj.name,
                is_binary=is_binary,
            )

        except (OSError, PermissionError):
            return None

    def _should_exclude(self, path: str, base_dir: str) -> bool:
        """Check if path should be excluded"""
        relative_path = os.path.relpath(path, base_dir)
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
            # Also check just the filename
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False

    def _should_include(self, file_info: FileInfo) -> bool:
        """Check if file should be included"""
        # Skip binary files
        if file_info.is_binary:
            return False

        # Include if extension matches
        if file_info.extension in self.include_extensions:
            return True

        # Include files without extension if they might be scripts
        if not file_info.extension:
            return self._might_be_script(file_info.path)

        return False

    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is binary by reading first chunk"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes (common in binary files)
                return b'\x00' in chunk
        except (OSError, PermissionError):
            return True

    def _might_be_script(self, file_path: str) -> bool:
        """Check if file without extension might be a script"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                # Check for shebang
                return first_line.startswith('#!')
        except (OSError, UnicodeDecodeError):
            return False

    def get_statistics(self, files: List[FileInfo]) -> Dict[str, Any]:
        """
        Get statistics about scanned files
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Dictionary with statistics
        """
        total_size = sum(f.size for f in files)
        extensions = {}
        
        for file_info in files:
            ext = file_info.extension or "no extension"
            extensions[ext] = extensions.get(ext, 0) + 1

        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "extensions": extensions,
            "largest_file": max(files, key=lambda f: f.size).to_dict() if files else None,
        }
