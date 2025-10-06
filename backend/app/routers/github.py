from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.database import User
from app.models.schemas import Repository
from app.services.github_service import GitHubService
from app.routers.auth import get_current_user_dependency

router = APIRouter()

@router.get("/repos", response_model=List[Repository])
async def get_user_repositories(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all repositories for the current user from GitHub"""
    try:
        github_service = GitHubService(current_user.github_token)
        repositories = github_service.get_user_repositories(current_user.id, db)
        return repositories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

@router.get("/repos/{repo_id}", response_model=Repository)
async def get_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get a specific repository by ID"""
    github_service = GitHubService(current_user.github_token)
    
    # Validate access
    if not github_service.validate_repository_access(repo_id, current_user.id):
        raise HTTPException(status_code=403, detail="No access to repository")
    
    repository = github_service.get_repository_by_id(repo_id)
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repository
