#!/usr/bin/env python3
"""
CodeGuard LangGraph - Simple Terminal Test
Run analysis pipeline without FastAPI - just pure Python.
"""
import asyncio
import sys
from pathlib import Path
from loguru import logger
import time

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

from config import settings, ensure_directories
from storage.sqlite_manager import SQLiteManager
from graphs.analysis_graph import get_analysis_graph


async def analyze_repository(repo_url: str, query: str = None):
    """
    Analyze a Git repository with LangGraph.
    
    Steps:
    1. Clones the repository
    2. Indexes files in SQLite
    3. Generates embeddings (BGE)
    4. Searches relevant code (HNSWlib)
    5. Queries LLM (Gemini)
    6. Returns analysis results
    """
    start_time = time.time()
    
    print("=" * 80)
    print("🚀 CodeGuard LangGraph Analysis")
    print("=" * 80)
    print(f"📦 Repository: {repo_url}")
    if query:
        print(f"💬 Query: {query}")
    print("=" * 80)
    print()
    
    try:
        # Prepare initial state
        initial_state = {
            "repo_url": repo_url,
            "query": query,
            "repo_id": None,
            "repo_name": None,
            "local_path": None,
            "commit_hash": None,
            "code_files": [],
            "total_files": 0,
            "chunks": [],
            "embeddings_generated": False,
            "embedding_ids": [],
            "relevant_chunks": [],
            "search_performed": False,
            "llm_response": None,
            "llm_context": None,
            "execution_time_ms": 0,
            "errors": [],
            "current_step": "start",
            "stats": {}
        }
        
        # Get LangGraph
        graph = get_analysis_graph()
        
        # Run the workflow
        print("⏳ Running LangGraph pipeline...\n")
        final_state = await graph.ainvoke(initial_state)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Display results
        print()
        print("=" * 80)
        print("✅ Analysis Complete!")
        print("=" * 80)
        print(f"📁 Repository: {final_state.get('repo_name', 'unknown')}")
        print(f"📄 Total Files: {final_state.get('total_files', 0)}")
        print(f"📝 Chunks: {len(final_state.get('chunks', []))}")
        print(f"🔍 Relevant Chunks: {len(final_state.get('relevant_chunks', []))}")
        print(f"⚡ Execution Time: {execution_time:.2f}s")
        
        if final_state.get('errors'):
            print("\n⚠️  Errors:")
            for error in final_state['errors']:
                print(f"   - {error}")
        
        if final_state.get('llm_response'):
            print("\n" + "=" * 80)
            print("🤖 AI Analysis:")
            print("=" * 80)
            print(final_state['llm_response'])
            print("=" * 80)
        
        print("\n✨ Done!\n")
        return final_state
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Analysis failed")
        return None


async def interactive_mode():
    """Interactive mode - ask multiple questions about repositories."""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         CodeGuard LangGraph - Interactive Analysis Tool         ║
║                                                                  ║
║  Analyze Git repositories and ask questions with AI             ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check API key
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        print("❌ ERROR: GEMINI_API_KEY not set in .env file")
        sys.exit(1)
    
    # Setup
    print("📁 Setting up directories...")
    ensure_directories()
    
    print("💾 Initializing database...")
    sqlite_manager = SQLiteManager()
    await sqlite_manager.initialize()
    print("✅ Ready!\n")
    
    current_repo = None
    
    while True:
        print("\n" + "=" * 80)
        print("📋 Menu:")
        print("  1. Analyze a new repository")
        print("  2. Ask a question about current repository")
        print("  3. Exit")
        print("=" * 80)
        
        choice = input("\n👉 Enter your choice (1-3): ").strip()
        
        if choice == "1":
            # Clone and analyze new repository
            repo_url = input("\n📦 Enter Git repository URL: ").strip()
            if not repo_url:
                print("❌ Invalid URL")
                continue
            
            query = input("💬 Enter your question (or press Enter to skip): ").strip()
            
            result = await analyze_repository(
                repo_url=repo_url,
                query=query if query else "Provide a high-level overview of this codebase"
            )
            
            if result and not result.get('errors'):
                current_repo = {
                    'url': repo_url,
                    'name': result.get('repo_name'),
                    'repo_id': result.get('repo_id')
                }
        
        elif choice == "2":
            # Ask question about current repository
            if not current_repo:
                print("\n❌ No repository loaded. Please analyze a repository first (Option 1)")
                continue
            
            print(f"\n📁 Current repository: {current_repo['name']}")
            query = input("💬 Enter your question: ").strip()
            
            if not query:
                print("❌ Question cannot be empty")
                continue
            
            # Query without re-cloning (embeddings already exist)
            await analyze_repository(
                repo_url=current_repo['url'],
                query=query
            )
        
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1, 2, or 3.")


async def main():
    """Main entry point."""
    try:
        await interactive_mode()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.exception("Fatal error")


if __name__ == "__main__":
    asyncio.run(main())
