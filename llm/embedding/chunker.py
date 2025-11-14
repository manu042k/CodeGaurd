"""Code chunking strategies for embedding."""
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from loguru import logger

from config import settings


class CodeChunker:
    """Chunks code files into semantic units for embedding."""
    
    def __init__(self, max_chunk_size: int = None, overlap: int = None):
        self.max_chunk_size = max_chunk_size or settings.max_chunk_size
        self.overlap = overlap or settings.chunk_overlap
    
    def chunk_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Chunk a file based on its language."""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.py']:
            return self._chunk_python(content)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            return self._chunk_javascript(content)
        else:
            return self._chunk_generic(content)
    
    def _chunk_python(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Python code by functions and classes."""
        chunks = []
        lines = content.split('\n')
        
        # Simple pattern-based chunking (can be enhanced with AST)
        current_chunk = []
        current_start = 0
        current_entity = None
        indent_level = 0
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            
            # Detect function or class definition
            if stripped.startswith('def ') or stripped.startswith('class '):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'start_line': current_start,
                        'end_line': i - 1,
                        'entity_name': current_entity,
                        'chunk_type': 'function' if current_entity and 'def' in str(current_entity) else 'class'
                    })
                
                # Start new chunk
                current_chunk = [line]
                current_start = i
                current_entity = stripped.split('(')[0].replace('def ', '').replace('class ', '').strip(':')
                indent_level = len(line) - len(stripped)
            
            elif current_chunk:
                # Continue current chunk if indented or not too large
                if len(line) - len(stripped) > indent_level or len('\n'.join(current_chunk)) < self.max_chunk_size:
                    current_chunk.append(line)
                else:
                    # Close current chunk
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'start_line': current_start,
                        'end_line': i - 1,
                        'entity_name': current_entity,
                        'chunk_type': 'function' if current_entity and 'def' in str(current_entity) else 'class'
                    })
                    current_chunk = [line]
                    current_start = i
                    current_entity = None
            else:
                current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'start_line': current_start,
                'end_line': len(lines) - 1,
                'entity_name': current_entity,
                'chunk_type': 'code'
            })
        
        return chunks if chunks else self._chunk_generic(content)
    
    def _chunk_javascript(self, content: str) -> List[Dict[str, Any]]:
        """Chunk JavaScript/TypeScript code."""
        chunks = []
        lines = content.split('\n')
        
        # Pattern for function/arrow function/class
        func_pattern = re.compile(r'(function\s+\w+|const\s+\w+\s*=|class\s+\w+|export\s+(default\s+)?(function|class))')
        
        current_chunk = []
        current_start = 0
        current_entity = None
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect function/class start
            match = func_pattern.search(line)
            if match and not current_chunk:
                current_entity = match.group(0)
                current_start = i
                current_chunk = [line]
                brace_count = line.count('{') - line.count('}')
            elif current_chunk:
                current_chunk.append(line)
                brace_count += line.count('{') - line.count('}')
                
                # End of function/class
                if brace_count == 0 and '{' in ''.join(current_chunk):
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'start_line': current_start,
                        'end_line': i,
                        'entity_name': current_entity,
                        'chunk_type': 'function'
                    })
                    current_chunk = []
                    current_entity = None
                    brace_count = 0
        
        return chunks if chunks else self._chunk_generic(content)
    
    def _chunk_generic(self, content: str) -> List[Dict[str, Any]]:
        """Generic chunking by line count."""
        lines = content.split('\n')
        chunks = []
        
        chunk_size_lines = self.max_chunk_size // 50  # Approximate lines
        overlap_lines = self.overlap // 50
        
        for i in range(0, len(lines), chunk_size_lines - overlap_lines):
            chunk_lines = lines[i:i + chunk_size_lines]
            if chunk_lines:
                chunks.append({
                    'content': '\n'.join(chunk_lines),
                    'start_line': i,
                    'end_line': min(i + chunk_size_lines - 1, len(lines) - 1),
                    'entity_name': None,
                    'chunk_type': 'block'
                })
        
        return chunks
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token count estimation (4 chars ≈ 1 token)."""
        return len(text) // 4
