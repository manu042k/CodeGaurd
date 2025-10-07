import git
import tempfile
import os
from sqlalchemy.orm import Session
from app.models.database import User, Project
from app.services.project_service import ProjectService
from app.services.github_service import GitHubService

class AnalysisService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    async def start_project_analysis(self, project_id: str) -> dict:
        """
        Starts the analysis of a project.
        1. Fetches project from DB.
        2. Clones the repository.
        3. (Future) Triggers analysis tasks.
        """
        project_service = ProjectService(self.db)
        project = project_service.get_project_by_id(project_id, self.user.id)

        if not project:
            raise ValueError("Project not found")

        if not project.github_full_name:
            raise ValueError("Repository not found for the project")

        github_service = GitHubService(self.user.github_token)
        repo_details = github_service.get_repo_details(project.github_full_name)
        is_private = repo_details.get("private", False)
        clone_url = repo_details.get("clone_url")

        if not clone_url:
            raise ValueError("Could not determine repository clone URL.")

        if is_private:
            token = self.user.github_token
            clone_url = clone_url.replace("https://", f"https://oauth2:{token}@")

        return self.clone_repository(clone_url)


    def clone_repository(self, repo_url: str) -> dict:
        """
        Clones a public repository into a temporary directory.
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            git.Repo.clone_from(repo_url, temp_dir)
            
            # For now, just return a success message with the path
            # In a real application, you might trigger an analysis task from here
            return {
                "message": "Repository cloned successfully",
                "temp_path": temp_dir
            }
        except git.exc.GitCommandError as e:
            # Handle clone errors (e.g., repo not found, access denied)
            # Clean up the temp directory
            os.rmdir(temp_dir)
            raise ValueError(f"Failed to clone repository: {e.stderr}")
        except Exception as e:
            os.rmdir(temp_dir)
            raise e
