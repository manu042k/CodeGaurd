"""LangGraph state definition for code analysis pipeline."""
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass


class AnalysisState(TypedDict):
    """State for the code analysis LangGraph."""
    
    # Input
    repo_url: str
    query: Optional[str]
    
    # Repository info
    repo_id: Optional[int]
    repo_name: Optional[str]
    local_path: Optional[str]
    commit_hash: Optional[str]
    
    # Files
    code_files: List[str]
    total_files: int
    
    # Chunking & Embedding
    chunks: List[Dict[str, Any]]
    embeddings_generated: bool
    embedding_ids: List[int]
    
    # Vector search results
    relevant_chunks: List[Dict[str, Any]]
    search_performed: bool
    
    # LLM Response
    llm_response: Optional[str]
    llm_context: Optional[List[str]]
    
    # Metadata
    execution_time_ms: int
    errors: List[str]
    current_step: str
    
    # Statistics
    stats: Dict[str, Any]
