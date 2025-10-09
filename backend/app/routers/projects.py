from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.database import User
from app.models.schemas import Project, ProjectCreate, ProjectUpdate, ProjectWithAnalysis
from app.services.project_service import ProjectService
from app.services.github_service import GitHubService
from app.routers.auth import get_current_user_dependency

router = APIRouter()

# Removed custom auth function, using get_current_user_dependency instead

@router.get("/", response_model=List[ProjectWithAnalysis])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    project_service = ProjectService(db)
    projects = project_service.get_projects_by_user(current_user.id, skip, limit)
    return projects

@router.get("/{project_id}", response_model=ProjectWithAnalysis)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get a specific project by ID"""
    project_service = ProjectService(db)
    project = project_service.get_project_by_id(project_id, current_user.id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@router.post("/", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project_service = ProjectService(db)
    
    try:
        # Validate repository access using GitHub API directly
        github_service = GitHubService(current_user.github_token, db)
        if not github_service.validate_repository_access_by_name(project_data.github_full_name):
            raise HTTPException(status_code=403, detail="No access to repository")
        
        project = project_service.create_project(project_data, current_user.id)
        return project
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        import traceback
        print(f"Project creation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Update an existing project"""
    project_service = ProjectService(db)
    project = project_service.update_project(project_id, project_data, current_user.id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    project_service = ProjectService(db)
    success = project_service.delete_project(project_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}


