"""LangGraph nodes for code analysis pipeline."""
import time
from pathlib import Path
from typing import Any, Dict
from loguru import logger

from graphs.state import AnalysisState
from services.git_manager import GitManager
from storage.sqlite_manager import SQLiteManager, compute_file_hash
from embedding.chunker import CodeChunker
from embedding.embedder import get_embedder
from embedding.vector_store import VectorStore


# Initialize components
git_manager = GitManager()
sqlite_manager = SQLiteManager()
chunker = CodeChunker()
embedder = get_embedder()
vector_store = VectorStore()


async def clone_repository_node(state: AnalysisState) -> AnalysisState:
    """Node 1: Clone Git repository."""
    logger.info(f"[CLONE] Starting repository clone: {state['repo_url']}")
    state['current_step'] = 'clone_repository'
    
    try:
        local_path, repo_name, commit_hash = git_manager.clone_repository(
            state['repo_url'],
            force=False
        )
        
        state['local_path'] = local_path
        state['repo_name'] = repo_name
        state['commit_hash'] = commit_hash
        
        logger.info(f"[CLONE] Repository cloned: {repo_name} at {local_path}")
        
    except Exception as e:
        logger.error(f"[CLONE] Failed to clone repository: {e}")
        state['errors'].append(f"Clone failed: {str(e)}")
    
    return state


async def index_repository_node(state: AnalysisState) -> AnalysisState:
    """Node 2: Index repository in SQLite."""
    logger.info(f"[INDEX] Indexing repository: {state['repo_name']}")
    state['current_step'] = 'index_repository'
    
    try:
        # Add repository to database
        repo_id = await sqlite_manager.add_repository(
            repo_url=state['repo_url'],
            repo_name=state['repo_name'],
            local_path=state['local_path'],
            git_commit_hash=state['commit_hash']
        )
        state['repo_id'] = repo_id
        
        # Get code files
        code_files = git_manager.get_code_files(state['local_path'])
        state['code_files'] = code_files
        state['total_files'] = len(code_files)
        
        logger.info(f"[INDEX] Found {len(code_files)} code files")
        
        # Index files in database
        for file_path in code_files:
            try:
                with open(file_path, 'rb') as f:
                    content_bytes = f.read()
                
                file_hash = compute_file_hash(content_bytes)
                file_size = len(content_bytes)
                language = git_manager.detect_language(file_path)
                relative_path = str(Path(file_path).relative_to(state['local_path']))
                
                await sqlite_manager.add_file(
                    repo_id=repo_id,
                    file_path=relative_path,
                    file_hash=file_hash,
                    file_size=file_size,
                    language=language
                )
                
            except Exception as e:
                logger.warning(f"[INDEX] Failed to index file {file_path}: {e}")
        
        logger.info(f"[INDEX] Repository indexed successfully")
        
    except Exception as e:
        logger.error(f"[INDEX] Failed to index repository: {e}")
        state['errors'].append(f"Indexing failed: {str(e)}")
    
    return state


async def generate_embeddings_node(state: AnalysisState) -> AnalysisState:
    """Node 3: Generate embeddings for code chunks."""
    logger.info(f"[EMBED] Generating embeddings for {state['total_files']} files")
    state['current_step'] = 'generate_embeddings'
    
    try:
        # Initialize vector store
        vector_store.initialize()
        
        all_chunks = []
        chunk_metadata = []
        
        # Process each file
        for file_path in state['code_files'][:100]:  # Limit for demo
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                relative_path = str(Path(file_path).relative_to(state['local_path']))
                
                # Chunk the file
                chunks = chunker.chunk_file(content, file_path)
                
                # Store chunks in database
                for idx, chunk in enumerate(chunks):
                    # Get file_id from database
                    # For simplicity, we'll store chunk content
                    chunk_text = chunk['content']
                    all_chunks.append(chunk_text)
                    chunk_metadata.append({
                        'file_path': relative_path,
                        'chunk_index': idx,
                        **chunk
                    })
                
            except Exception as e:
                logger.warning(f"[EMBED] Failed to process file {file_path}: {e}")
        
        logger.info(f"[EMBED] Generated {len(all_chunks)} chunks")
        
        # Generate embeddings in batches
        if all_chunks:
            embeddings = embedder.embed_batch(all_chunks)
            
            # Add to vector store
            embedding_ids = vector_store.add_vectors(embeddings)
            
            # Save vector store
            vector_store.save()
            
            state['chunks'] = chunk_metadata
            state['embeddings_generated'] = True
            state['embedding_ids'] = embedding_ids
            
            logger.info(f"[EMBED] Embeddings generated and stored")
        
    except Exception as e:
        logger.error(f"[EMBED] Failed to generate embeddings: {e}")
        state['errors'].append(f"Embedding generation failed: {str(e)}")
    
    return state


async def search_relevant_code_node(state: AnalysisState) -> AnalysisState:
    """Node 4: Search for relevant code based on query."""
    query = state.get('query')
    
    if not query:
        logger.info("[SEARCH] No query provided, skipping search")
        state['relevant_chunks'] = state.get('chunks', [])[:10]  # Return first 10
        state['search_performed'] = False
        return state
    
    logger.info(f"[SEARCH] Searching for: {query}")
    state['current_step'] = 'search_code'
    
    try:
        # Load vector store
        vector_store.initialize()
        
        # Generate query embedding
        query_embedding = embedder.embed_text(query)
        
        # Search for similar chunks
        ids, scores = vector_store.search(query_embedding, k=10)
        
        # Get chunk metadata
        chunks = state.get('chunks', [])
        relevant_chunks = []
        
        for idx, score in zip(ids, scores):
            if idx < len(chunks):
                chunk_data = chunks[idx].copy()
                chunk_data['similarity_score'] = score
                relevant_chunks.append(chunk_data)
        
        state['relevant_chunks'] = relevant_chunks
        state['search_performed'] = True
        
        logger.info(f"[SEARCH] Found {len(relevant_chunks)} relevant chunks")
        
    except Exception as e:
        logger.error(f"[SEARCH] Search failed: {e}")
        state['errors'].append(f"Search failed: {str(e)}")
        state['relevant_chunks'] = []
    
    return state


async def query_llm_node(state: AnalysisState) -> AnalysisState:
    """Node 5: Query Gemini LLM with relevant context."""
    logger.info("[LLM] Querying Gemini with code context")
    state['current_step'] = 'query_llm'
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from config import settings
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            google_api_key=settings.gemini_api_key
        )
        
        # Build context from relevant chunks
        relevant_chunks = state.get('relevant_chunks', [])
        context_parts = []
        
        for i, chunk in enumerate(relevant_chunks[:5], 1):  # Top 5
            context_parts.append(
                f"--- Code Chunk {i} ({chunk.get('file_path', 'unknown')}) ---\n"
                f"{chunk.get('content', '')}\n"
            )
        
        context = "\n".join(context_parts)
        state['llm_context'] = context_parts
        
        # Build prompt
        query = state.get('query', 'Analyze this code')
        
        prompt = f"""You are a code analysis expert. Analyze the following code from repository: {state.get('repo_name')}

Repository Information:
- Total Files: {state.get('total_files', 0)}
- Commit: {state.get('commit_hash', 'unknown')[:8]}

User Query: {query}

Relevant Code Context:
{context}

Please provide a detailed analysis answering the user's query. Include:
1. Direct answer to the query
2. Relevant code examples or patterns found
3. Any potential issues or improvements
4. Summary of findings
"""
        
        # Query LLM
        response = llm.invoke(prompt)
        state['llm_response'] = response.content
        
        logger.info("[LLM] Response generated successfully")
        
    except Exception as e:
        logger.error(f"[LLM] Query failed: {e}")
        state['errors'].append(f"LLM query failed: {str(e)}")
        state['llm_response'] = f"Error: {str(e)}"
    
    return state


async def finalize_analysis_node(state: AnalysisState) -> AnalysisState:
    """Node 6: Finalize analysis and gather statistics."""
    logger.info("[FINALIZE] Finalizing analysis")
    state['current_step'] = 'finalize'
    
    try:
        # Get repository stats
        if state.get('repo_id'):
            stats = await sqlite_manager.get_stats(state['repo_id'])
            state['stats'] = stats
        
        # Save session
        if state.get('repo_id') and state.get('llm_response'):
            await sqlite_manager.save_analysis_session(
                repo_id=state['repo_id'],
                query=state.get('query', ''),
                results={
                    'response': state['llm_response'],
                    'relevant_chunks': len(state.get('relevant_chunks', [])),
                    'total_chunks': len(state.get('chunks', []))
                },
                execution_time_ms=state.get('execution_time_ms', 0)
            )
        
        logger.info("[FINALIZE] Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"[FINALIZE] Finalization failed: {e}")
        state['errors'].append(f"Finalization failed: {str(e)}")
    
    return state
