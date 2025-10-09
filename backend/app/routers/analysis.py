"""
Analysis Router - FastAPI endpoints for the LLM-powered static analysis platform
"""
import os
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel
from git import Repo
from app.services.results_aggregator import results_aggregator

router = APIRouter()

# Request/Response Models
class AnalysisRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    agents: Optional[List[str]] = None  # None means all agents
    context: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    success: bool
    result_id: Optional[str] = None
    message: str
    error: Optional[str] = None

class ResultSummary(BaseModel):
    result_id: str
    repo_path: str
    overall_score: Optional[float]
    timestamp: Optional[str]
    stored_at: str
    success: bool
    agents_executed: List[str]
    total_issues: int

@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Start a new repository analysis"""
    try:
        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp(prefix="codeguard_analysis_")
        
        try:
            # Clone the repository
            repo = Repo.clone_from(
                request.repo_url,
                temp_dir,
                branch=request.branch,
                depth=1  # Shallow clone for faster analysis
            )
            
            # Run analysis in background
            if request.agents:
                # Selective analysis
                background_tasks.add_task(
                    _run_selective_analysis,
                    temp_dir,
                    request.agents,
                    request.context
                )
                message = f"Started selective analysis with {len(request.agents)} agents"
            else:
                # Full analysis
                background_tasks.add_task(
                    _run_full_analysis,
                    temp_dir,
                    request.context
                )
                message = "Started full analysis with all agents"
            
            return AnalysisResponse(
                success=True,
                message=message
            )
        
        except Exception as e:
            # Cleanup on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to start analysis",
            error=str(e)
        )

@router.post("/analyze-sync", response_model=Dict[str, Any])
async def analyze_sync(request: AnalysisRequest):
    """Run analysis synchronously and return results immediately"""
    temp_dir = None
    try:
        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp(prefix="codeguard_analysis_")
        
        # Clone the repository
        repo = Repo.clone_from(
            request.repo_url,
            temp_dir,
            branch=request.branch,
            depth=1
        )
        
        # Run analysis
        if request.agents:
            results = await results_aggregator.run_selective_analysis(
                temp_dir, request.agents, request.context
            )
        else:
            results = await results_aggregator.run_full_analysis(
                temp_dir, request.context
            )
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/results/{result_id}", response_model=Dict[str, Any])
async def get_analysis_results(result_id: str = Path(..., description="Analysis result ID")):
    """Get analysis results by ID"""
    results = results_aggregator.get_results(result_id)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis results not found for ID: {result_id}"
        )
    
    return results

@router.get("/results", response_model=List[ResultSummary])
async def list_analysis_results(
    repo_path: Optional[str] = Query(None, description="Filter by repository path"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results to return")
):
    """List stored analysis results"""
    results = results_aggregator.list_results(repo_path, limit)
    return results

@router.delete("/results/{result_id}")
async def delete_analysis_results(result_id: str = Path(..., description="Analysis result ID")):
    """Delete analysis results by ID"""
    success = results_aggregator.delete_results(result_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis results not found for ID: {result_id}"
        )
    
    return {"message": f"Analysis results deleted successfully: {result_id}"}

@router.get("/trends/{repo_path:path}")
async def get_trend_report(
    repo_path: str = Path(..., description="Repository path"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get trend analysis report for a repository"""
    try:
        report = results_aggregator.get_trend_report(repo_path, days)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate trend report: {str(e)}"
        )

@router.get("/agents/status")
async def get_agent_status():
    """Get status of all analysis agents"""
    try:
        status = results_aggregator.get_agent_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Perform system health check"""
    try:
        health = await results_aggregator.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_results(
    days_to_keep: int = Query(90, ge=1, le=365, description="Number of days to keep results")
):
    """Clean up old analysis results and trend data"""
    try:
        results_aggregator.cleanup_old_results(days_to_keep)
        return {"message": f"Cleanup completed, kept results from last {days_to_keep} days"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )

# Background task functions
async def _run_full_analysis(repo_path: str, context: Optional[Dict] = None):
    """Background task for full analysis"""
    try:
        await results_aggregator.run_full_analysis(repo_path, context)
    except Exception as e:
        print(f"Background analysis failed: {e}")
    finally:
        # Cleanup temporary directory
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

async def _run_selective_analysis(repo_path: str, agent_names: List[str], context: Optional[Dict] = None):
    """Background task for selective analysis"""
    try:
        await results_aggregator.run_selective_analysis(repo_path, agent_names, context)
    except Exception as e:
        print(f"Background selective analysis failed: {e}")
    finally:
        # Cleanup temporary directory
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
