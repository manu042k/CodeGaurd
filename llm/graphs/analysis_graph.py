"""LangGraph workflow for code analysis."""
from langgraph.graph import StateGraph, END
from loguru import logger

from graphs.state import AnalysisState
from graphs.nodes import (
    clone_repository_node,
    index_repository_node,
    generate_embeddings_node,
    search_relevant_code_node,
    query_llm_node,
    finalize_analysis_node
)


def create_analysis_graph():
    """Create the LangGraph workflow for code analysis."""
    
    # Create graph
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("clone_repository", clone_repository_node)
    workflow.add_node("index_repository", index_repository_node)
    workflow.add_node("generate_embeddings", generate_embeddings_node)
    workflow.add_node("search_code", search_relevant_code_node)
    workflow.add_node("query_llm", query_llm_node)
    workflow.add_node("finalize", finalize_analysis_node)
    
    # Define edges (linear flow for now)
    workflow.set_entry_point("clone_repository")
    workflow.add_edge("clone_repository", "index_repository")
    workflow.add_edge("index_repository", "generate_embeddings")
    workflow.add_edge("generate_embeddings", "search_code")
    workflow.add_edge("search_code", "query_llm")
    workflow.add_edge("query_llm", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("LangGraph workflow created successfully")
    return app


# Global graph instance
analysis_graph = None


def get_analysis_graph():
    """Get or create the analysis graph."""
    global analysis_graph
    if analysis_graph is None:
        analysis_graph = create_analysis_graph()
    return analysis_graph
