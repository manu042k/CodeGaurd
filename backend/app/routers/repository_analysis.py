"""
Repository Analysis API Router
Endpoints for cloning and analyzing GitHub repositories
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..models.database import User, Repository
from ..services.github_service import GitHubService
from ..services.repository_analysis_service import RepositoryAnalysisService
from ..coordinator import AnalysisConfig
from ..routers.auth import get_current_user_dependency

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRepositoryRequest(BaseModel):
    """Request model for repository analysis"""
    repository_id: int
    shallow_clone: bool = True
    use_llm: bool = False
    enabled_agents: Optional[list[str]] = ["security", "dependency"]


class AnalyzeRepositoryResponse(BaseModel):
    """Response model for repository analysis"""
    status: str
    message: str
    report: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=AnalyzeRepositoryResponse)
async def analyze_repository(
    request: AnalyzeRepositoryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Clone and analyze a GitHub repository
    
    This endpoint:
    1. Clones the repository from GitHub
    2. Runs multi-agent code analysis
    3. Returns a comprehensive security and quality report
    4. Cleans up the cloned files
    
    Args:
        request: Analysis request parameters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Complete analysis report with findings and recommendations
    """
    try:
        # Get repository from database
        repository = db.query(Repository).filter(
            Repository.id == request.repository_id
        ).first()
        
        if not repository:
            raise HTTPException(
                status_code=404,
                detail=f"Repository {request.repository_id} not found"
            )
        
        # Verify user has access to this repository
        github_service = GitHubService(current_user.github_token, db)
        
        # Configure analysis
        analysis_config = AnalysisConfig(
            max_concurrent_files=10,
            timeout_per_file=30,
            use_llm=request.use_llm,
            enabled_agents=request.enabled_agents or ["security", "dependency"],
        )
        
        # Create analysis service
        analysis_service = RepositoryAnalysisService(
            github_service=github_service,
            analysis_config=analysis_config,
        )
        
        logger.info(
            f"Starting analysis for repository {repository.full_name} "
            f"(user: {current_user.username})"
        )
        
        # Run clone and analysis
        report = await analysis_service.clone_and_analyze(
            repository=repository,
            shallow=request.shallow_clone,
            cleanup=True,
        )
        
        if report["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=report.get("error", "Analysis failed")
            )
        
        # Return success response
        return AnalyzeRepositoryResponse(
            status="success",
            message=f"Successfully analyzed {repository.full_name}",
            report=report,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_repository endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/analyze/{repository_id}/status")
async def get_analysis_status(
    repository_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Get the status of a repository analysis
    (Placeholder for future async task tracking)
    """
    # TODO: Implement with Celery task tracking
    return {
        "repository_id": repository_id,
        "status": "not_implemented",
        "message": "Task tracking not yet implemented"
    }


@router.post("/analyze-batch")
async def analyze_multiple_repositories(
    repository_ids: list[int],
    shallow_clone: bool = True,
    use_llm: bool = False,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    Analyze multiple repositories in batch
    (For future implementation)
    """
    # TODO: Implement batch analysis with Celery
    return {
        "status": "not_implemented",
        "message": "Batch analysis will be implemented with task queue",
        "repository_count": len(repository_ids)
    }
