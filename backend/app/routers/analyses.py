from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import User
from app.routers.auth import get_current_user_dependency
from app.services.analysis_service import AnalysisService
from pydantic import BaseModel

router = APIRouter()

class AnalysisRequest(BaseModel):
    project_id: str

@router.post("/")
async def start_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Starts a new analysis for a given project.
    """
    analysis_service = AnalysisService(db=db, user=current_user)
    try:
        # The service method will handle the cloning and return some status
        result = await analysis_service.start_project_analysis(request.project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
