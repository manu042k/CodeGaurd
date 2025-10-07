"""
Language Detector
Detects programming language from file extension and content.
"""

import os
from typing import Optional, Dict
import re


class LanguageDetector:
    """Detects programming language of files"""

    # Extension to language mapping
    EXTENSION_MAP = {
        # Python
        ".py": "python",
        ".pyw": "python",
        ".pyx": "python",
        
        # JavaScript/TypeScript
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        
        # Java/Kotlin/Scala
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".scala": "scala",
        
        # C/C++
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
        ".c++": "cpp",
        ".h++": "cpp",
        
        # C#
        ".cs": "csharp",
        
        # Go
        ".go": "go",
        
        # Rust
        ".rs": "rust",
        
        # Ruby
        ".rb": "ruby",
        ".rake": "ruby",
        
        # PHP
        ".php": "php",
        ".phtml": "php",
        
        # Swift
        ".swift": "swift",
        
        # Objective-C
        ".m": "objective-c",
        ".mm": "objective-c",
        
        # Shell
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        
        # PowerShell
        ".ps1": "powershell",
        ".psm1": "powershell",
        
        # SQL
        ".sql": "sql",
        
        # HTML/CSS
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        
        # Vue/Svelte
        ".vue": "vue",
        ".svelte": "svelte",
        
        # Dart
        ".dart": "dart",
        
        # R
        ".r": "r",
        ".R": "r",
        
        # Lua
        ".lua": "lua",
        
        # Perl
        ".pl": "perl",
        ".pm": "perl",
        ".perl": "perl",
        
        # Haskell
        ".hs": "haskell",
        ".lhs": "haskell",
        
        # Elixir
        ".ex": "elixir",
        ".exs": "elixir",
        
        # Clojure
        ".clj": "clojure",
        ".cljs": "clojure",
        ".cljc": "clojure",
        
        # Elm
        ".elm": "elm",
        
        # Erlang
        ".erl": "erlang",
        ".hrl": "erlang",
        
        # F#
        ".fs": "fsharp",
        ".fsx": "fsharp",
        ".fsi": "fsharp",
        
        # OCaml
        ".ml": "ocaml",
        ".mli": "ocaml",
        
        # Nim
        ".nim": "nim",
        
        # Zig
        ".zig": "zig",
        
        # YAML/JSON/XML
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        
        # Markdown
        ".md": "markdown",
        ".markdown": "markdown",
        
        # Config files
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "conf",
    }

    # Filename to language mapping (for files without extension)
    FILENAME_MAP = {
        "Dockerfile": "dockerfile",
        "Makefile": "makefile",
        "Rakefile": "ruby",
        "Gemfile": "ruby",
        "Vagrantfile": "ruby",
        "CMakeLists.txt": "cmake",
        ".bashrc": "shell",
        ".zshrc": "shell",
        ".bash_profile": "shell",
    }

    # Shebang to language mapping
    SHEBANG_MAP = {
        "python": "python",
        "python3": "python",
        "node": "javascript",
        "ruby": "ruby",
        "perl": "perl",
        "bash": "shell",
        "sh": "shell",
        "zsh": "shell",
        "php": "php",
    }

    @classmethod
    def detect_language(cls, file_path: str, content: Optional[str] = None) -> str:
        """
        Detect programming language from file path and content
        
        Args:
            file_path: Path to the file
            content: File content (optional, used for shebang detection)
            
        Returns:
            Language identifier (lowercase)
        """
        # Try extension-based detection
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]

        # Try filename-based detection
        filename = os.path.basename(file_path)
        if filename in cls.FILENAME_MAP:
            return cls.FILENAME_MAP[filename]

        # Try shebang detection if content is provided
        if content:
            language = cls._detect_from_shebang(content)
            if language:
                return language

        # Default to "unknown"
        return "unknown"

    @classmethod
    def _detect_from_shebang(cls, content: str) -> Optional[str]:
        """Detect language from shebang line"""
        lines = content.split('\n', 1)
        if not lines or not lines[0].startswith('#!'):
            return None

        shebang = lines[0][2:].strip()
        
        # Extract interpreter name
        for pattern, language in cls.SHEBANG_MAP.items():
            if pattern in shebang.lower():
                return language

        return None

    @classmethod
    def is_supported(cls, language: str) -> bool:
        """
        Check if a language is supported for analysis
        
        Args:
            language: Language identifier
            
        Returns:
            True if language is supported
        """
        # For now, consider all detected languages as supported
        # Individual agents will decide if they can handle specific languages
        return language != "unknown"

    @classmethod
    def get_language_info(cls, language: str) -> Dict[str, any]:
        """
        Get information about a language
        
        Args:
            language: Language identifier
            
        Returns:
            Dictionary with language information
        """
        language_info = {
            "python": {
                "name": "Python",
                "type": "interpreted",
                "paradigm": ["object-oriented", "procedural", "functional"],
                "extensions": [".py", ".pyw", ".pyx"],
            },
            "javascript": {
                "name": "JavaScript",
                "type": "interpreted",
                "paradigm": ["object-oriented", "functional", "event-driven"],
                "extensions": [".js", ".jsx", ".mjs", ".cjs"],
            },
            "typescript": {
                "name": "TypeScript",
                "type": "compiled",
                "paradigm": ["object-oriented", "functional"],
                "extensions": [".ts", ".tsx"],
            },
            "java": {
                "name": "Java",
                "type": "compiled",
                "paradigm": ["object-oriented"],
                "extensions": [".java"],
            },
            "go": {
                "name": "Go",
                "type": "compiled",
                "paradigm": ["procedural", "concurrent"],
                "extensions": [".go"],
            },
            "rust": {
                "name": "Rust",
                "type": "compiled",
                "paradigm": ["functional", "procedural"],
                "extensions": [".rs"],
            },
            "cpp": {
                "name": "C++",
                "type": "compiled",
                "paradigm": ["object-oriented", "procedural"],
                "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            },
            "csharp": {
                "name": "C#",
                "type": "compiled",
                "paradigm": ["object-oriented", "functional"],
                "extensions": [".cs"],
            },
        }

        return language_info.get(language, {
            "name": language.capitalize(),
            "type": "unknown",
            "paradigm": [],
            "extensions": [],
        })

    @classmethod
    def get_all_supported_languages(cls) -> list[str]:
        """Get list of all supported languages"""
        languages = set(cls.EXTENSION_MAP.values())
        languages.update(cls.FILENAME_MAP.values())
        languages.update(cls.SHEBANG_MAP.values())
        return sorted(list(languages))

    @classmethod
    def get_extensions_for_language(cls, language: str) -> list[str]:
        """Get file extensions for a given language"""
        return [ext for ext, lang in cls.EXTENSION_MAP.items() if lang == language]
