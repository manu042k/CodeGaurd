from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.schemas import ProjectCreate, ProjectUpdate
from app.models.database import Project, User, Analysis
import uuid

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_projects_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects for a user with their latest analysis"""
        projects = (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Add latest analysis to each project
        for project in projects:
            latest_analysis = (
                self.db.query(Analysis)
                .filter(Analysis.project_id == project.id)
                .order_by(Analysis.started_at.desc())
                .first()
            )
            project.latest_analysis = latest_analysis
            
        return projects
    
    def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a specific project by ID for a user"""
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.user_id == user_id)
            .first()
        )
        
        if project:
            # Add latest analysis
            latest_analysis = (
                self.db.query(Analysis)
                .filter(Analysis.project_id == project.id)
                .order_by(Analysis.started_at.desc())
                .first()
            )
            project.latest_analysis = latest_analysis
            
        return project
    
    def create_project(self, project_data: ProjectCreate, user_id: str) -> Project:
        """Create a new project"""
        try:
            # Create the project directly with GitHub repository info
            db_project = Project(
                id=str(uuid.uuid4()),
                name=project_data.name,
                description=project_data.description,
                user_id=user_id,
                github_repo_id=project_data.github_repo_id,
                github_url=project_data.github_url,
                github_full_name=project_data.github_full_name,
                settings=project_data.settings.dict() if project_data.settings else None
            )
            
            self.db.add(db_project)
            self.db.commit()
            self.db.refresh(db_project)
            
            return db_project
            
        except Exception as e:
            print(f"ProjectService.create_project error: {str(e)}")
            self.db.rollback()
            raise
    
    def update_project(self, project_id: str, project_data: ProjectUpdate, user_id: str) -> Optional[Project]:
        """Update an existing project"""
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.user_id == user_id)
            .first()
        )
        
        if not project:
            return None
        
        # Update fields
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.settings is not None:
            project.settings = project_data.settings.dict()
        
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete a project"""
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.user_id == user_id)
            .first()
        )
        
        if not project:
            return False
        
        self.db.delete(project)
        self.db.commit()
        
        return True
    
    def update_project_status(self, project_id: str, status: str) -> Optional[Project]:
        """Update project status"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        
        if project:
            project.status = status
            self.db.commit()
            self.db.refresh(project)
        
        return project
    
    def increment_analysis_count(self, project_id: str):
        """Increment the analysis count for a project"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        
        if project:
            project.analysis_count = (project.analysis_count or 0) + 1
            self.db.commit()
