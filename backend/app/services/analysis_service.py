from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.database import Analysis, Project, AgentResult, User
from app.models.schemas import AnalysisCreate, AnalysisStatusResponse, AnalysisStatus, AgentType
from app.services.github_service import GitHubService
from app.core.config import settings
import logging
import os
import tempfile
import shutil

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_analysis(self, analysis_data: AnalysisCreate, user_id: str) -> Analysis:
        """Create a new analysis"""
        # Verify project exists and belongs to user
        project = self.db.query(Project).filter(
            Project.id == analysis_data.project_id,
            Project.user_id == user_id
        ).first()
        
        if not project:
            raise ValueError("Project not found")
        
        # Create analysis
        analysis = Analysis(
            project_id=analysis_data.project_id,
            status=AnalysisStatus.PENDING
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        # Create agent results for enabled agents
        enabled_agents = analysis_data.agent_types or [
            AgentType.CODE_QUALITY,
            AgentType.SECURITY,
            AgentType.ARCHITECTURE,
            AgentType.DOCUMENTATION
        ]
        
        for agent_type in enabled_agents:
            agent_result = AgentResult(
                analysis_id=analysis.id,
                agent_name=agent_type,
                status=AnalysisStatus.PENDING
            )
            self.db.add(agent_result)
        
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    def get_analysis_by_id(self, analysis_id: str, user_id: str) -> Optional[Analysis]:
        """Get analysis by ID if user has access"""
        return self.db.query(Analysis).join(Project).filter(
            Analysis.id == analysis_id,
            Project.user_id == user_id
        ).first()
    
    def get_analysis_status(self, analysis_id: str, user_id: str) -> Optional[AnalysisStatusResponse]:
        """Get analysis status and progress"""
        analysis = self.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis:
            return None
        
        # Calculate progress
        total_agents = len(analysis.agent_results)
        completed_agents = sum(1 for agent in analysis.agent_results 
                             if agent.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED])
        
        progress = int((completed_agents / total_agents) * 100) if total_agents > 0 else 0
        
        # Find current running agent
        current_agent = None
        for agent in analysis.agent_results:
            if agent.status == AnalysisStatus.RUNNING:
                current_agent = agent.agent_name
                break
        
        message = None
        if analysis.status == AnalysisStatus.FAILED:
            message = analysis.error
        elif analysis.status == AnalysisStatus.RUNNING and current_agent:
            message = f"Running {current_agent} analysis..."
        elif analysis.status == AnalysisStatus.COMPLETED:
            message = "Analysis completed successfully"
        
        return AnalysisStatusResponse(
            status=analysis.status,
            progress=progress,
            current_agent=current_agent,
            message=message
        )
    
    def cancel_analysis(self, analysis_id: str, user_id: str) -> bool:
        """Cancel a running analysis"""
        analysis = self.get_analysis_by_id(analysis_id, user_id)
        
        if not analysis or analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
            return False
        
        analysis.status = AnalysisStatus.CANCELLED
        analysis.completed_at = datetime.utcnow()
        
        # Update agent results
        for agent_result in analysis.agent_results:
            if agent_result.status in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
                agent_result.status = AnalysisStatus.CANCELLED
                agent_result.completed_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def run_analysis_background(self, analysis_id: str, github_token: str):
        """Run analysis in background (called by BackgroundTasks)"""
        try:
            analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return
            
            # Update status to running
            analysis.status = AnalysisStatus.RUNNING
            self.db.commit()
            
            # Get project and repository info
            project = analysis.project
            repository = project.repository
            
            # Clone repository to temporary directory
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp(prefix="codeguard_analysis_")
                
                github_service = GitHubService(github_token)
                clone_success = github_service.clone_repository(repository, temp_dir)
                
                if not clone_success:
                    raise Exception("Failed to clone repository")
                
                # Run each agent
                for agent_result in analysis.agent_results:
                    if analysis.status == AnalysisStatus.CANCELLED:
                        break
                    
                    await self._run_agent_analysis(agent_result, temp_dir, project.settings)
                
                # Calculate overall score and update analysis
                self._finalize_analysis(analysis)
                
            finally:
                # Clean up temporary directory
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {str(e)}")
            
            # Update analysis with error
            analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error = str(e)
                analysis.completed_at = datetime.utcnow()
                self.db.commit()
    
    async def _run_agent_analysis(self, agent_result: AgentResult, code_path: str, project_settings: dict):
        """Run analysis for a specific agent"""
        try:
            agent_result.status = AnalysisStatus.RUNNING
            agent_result.started_at = datetime.utcnow()
            self.db.commit()
            
            # For now, simulate analysis with mock results
            # In a real implementation, this would call actual analysis tools
            await self._run_mock_analysis(agent_result, code_path, project_settings)
            
            agent_result.status = AnalysisStatus.COMPLETED
            agent_result.completed_at = datetime.utcnow()
            
            if agent_result.started_at:
                duration = (agent_result.completed_at - agent_result.started_at).total_seconds()
                agent_result.duration = int(duration)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Agent {agent_result.agent_name} failed: {str(e)}")
            agent_result.status = AnalysisStatus.FAILED
            agent_result.error = str(e)
            agent_result.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def _run_mock_analysis(self, agent_result: AgentResult, code_path: str, project_settings: dict):
        """Mock analysis implementation - replace with real analysis logic"""
        import asyncio
        import random
        
        # Simulate analysis time
        await asyncio.sleep(random.uniform(2, 8))
        
        # Generate mock score and summary
        agent_result.score = random.uniform(0.6, 0.95)
        
        if agent_result.agent_name == AgentType.CODE_QUALITY:
            agent_result.summary = "Code quality analysis completed. Found potential improvements in code structure and maintainability."
        elif agent_result.agent_name == AgentType.SECURITY:
            agent_result.summary = "Security analysis completed. No critical vulnerabilities found."
        elif agent_result.agent_name == AgentType.ARCHITECTURE:
            agent_result.summary = "Architecture analysis completed. Code structure follows good patterns."
        elif agent_result.agent_name == AgentType.DOCUMENTATION:
            agent_result.summary = "Documentation analysis completed. Some functions could benefit from better documentation."
    
    def _finalize_analysis(self, analysis: Analysis):
        """Calculate overall score and finalize analysis"""
        completed_agents = [agent for agent in analysis.agent_results 
                          if agent.status == AnalysisStatus.COMPLETED and agent.score is not None]
        
        if completed_agents:
            # Calculate weighted average score
            total_score = sum(agent.score for agent in completed_agents)
            analysis.overall_score = total_score / len(completed_agents)
            
            analysis.summary = f"Analysis completed. Overall score: {analysis.overall_score:.2f}/1.00"
        else:
            analysis.overall_score = 0.0
            analysis.summary = "Analysis completed with no successful agent results"
        
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.utcnow()
        
        if analysis.started_at:
            duration = (analysis.completed_at - analysis.started_at).total_seconds()
            analysis.duration = int(duration)
        
        # Update project analysis count and status
        project = analysis.project
        project.analysis_count = project.analysis_count + 1
        project.status = "completed"
        
        self.db.commit()
