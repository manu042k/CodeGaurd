from celery import current_app as celery_app
from app.services.analysis_service import AnalysisService
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="analyze_code")
def analyze_code_task(self, project_id: int, file_paths: list = None):
    """
    Celery task to analyze code asynchronously
    """
    try:
        logger.info(f"Starting code analysis for project {project_id}")
        
        # Create analysis service instance
        analysis_service = AnalysisService()
        
        # Perform analysis
        result = analysis_service.analyze_project(project_id, file_paths)
        
        logger.info(f"Completed code analysis for project {project_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Analysis failed for project {project_id}: {str(exc)}")
        # Retry the task up to 3 times with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@celery_app.task(name="health_check")
def health_check():
    """
    Simple health check task
    """
    return {"status": "healthy", "message": "Celery worker is running"}
