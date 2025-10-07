from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.database import User
from app.models.schemas import Analysis, AnalysisCreate, AnalysisStatusResponse
from app.services.project_service import ProjectService
from app.services.analysis_service import AnalysisService
from app.routers.auth import get_current_user_dependency

router = APIRouter()

@router.post("/", response_model=Analysis)
async def create_analysis(
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create and start a new analysis"""
    # Verify project ownership
    project_service = ProjectService(db)
    project = project_service.get_project_by_id(analysis_data.project_id, current_user.id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create analysis
    analysis_service = AnalysisService(db)
    analysis = analysis_service.create_analysis(analysis_data, current_user.id)
    
    # Start analysis in background
    background_tasks.add_task(
        analysis_service.run_analysis_background,
        analysis.id,
        current_user.github_token
    )
    
    return analysis

@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get analysis by ID"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Fetching analysis: {analysis_id} for user: {current_user.username}")
    
    analysis_service = AnalysisService(db)
    analysis = analysis_service.get_analysis_by_id(analysis_id, current_user.id)
    
    if not analysis:
        logger.warning(f"❌ Analysis not found: {analysis_id}")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    logger.info(f"✅ Analysis found: {analysis_id}, status: {analysis.status}, agents: {len(analysis.agent_results)}")
    
    return analysis

@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get analysis status and progress"""
    analysis_service = AnalysisService(db)
    status = analysis_service.get_analysis_status(analysis_id, current_user.id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return status

@router.delete("/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Cancel a running analysis"""
    analysis_service = AnalysisService(db)
    success = analysis_service.cancel_analysis(analysis_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found or cannot be cancelled")
    
    return {"message": "Analysis cancelled successfully"}
