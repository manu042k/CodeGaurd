from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    NEVER_ANALYZED = "never_analyzed"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(str, Enum):
    CODE_QUALITY = "CodeQuality"
    SECURITY = "Security"
    ARCHITECTURE = "Architecture"
    DOCUMENTATION = "Documentation"

class IssueType(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Repository Schemas
class RepositoryBase(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool
    html_url: str
    clone_url: str
    language: Optional[str] = None
    stargazers_count: int
    forks_count: int
    owner_login: str
    owner_avatar_url: str
    created_at: datetime
    updated_at: datetime

class Repository(RepositoryBase):
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    github_id: str
    github_token: str

class User(UserBase):
    id: str
    github_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Project Schemas
class ProjectSettings(BaseModel):
    analysisConfig: Dict[str, Any] = Field(default={
        "enabledAgents": ["CodeQuality", "Security", "Architecture", "Documentation"],
        "excludePatterns": ["node_modules", "*.test.*", "dist", "build"],
        "includePaths": ["src", "lib", "pages", "components"]
    })
    notifications: Dict[str, bool] = Field(default={
        "onComplete": True,
        "onFailure": True
    })

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None

class ProjectCreate(ProjectBase):
    repository_id: int

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None

class Project(ProjectBase):
    id: str
    user_id: str
    repository_id: int
    status: ProjectStatus
    analysis_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    repository: Repository
    
    class Config:
        from_attributes = True

# Issue Schemas
class IssueBase(BaseModel):
    type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule: Optional[str] = None

class Issue(IssueBase):
    id: str
    agent_result_id: str
    
    class Config:
        from_attributes = True

# Agent Result Schemas
class AgentResultBase(BaseModel):
    agent_name: AgentType
    status: AnalysisStatus
    score: Optional[float] = None
    summary: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    error: Optional[str] = None

class AgentResult(AgentResultBase):
    id: str
    analysis_id: str
    issues: List[Issue] = []
    
    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisBase(BaseModel):
    status: AnalysisStatus = AnalysisStatus.PENDING
    overall_score: Optional[float] = None
    summary: Optional[str] = None

class AnalysisCreate(BaseModel):
    project_id: str
    agent_types: Optional[List[AgentType]] = None

class Analysis(AnalysisBase):
    id: str
    project_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    error: Optional[str] = None
    agent_results: List[AgentResult] = []
    
    class Config:
        from_attributes = True

# Extended Project with Latest Analysis
class ProjectWithAnalysis(Project):
    latest_analysis: Optional[Analysis] = None

# API Response Schemas
class ProjectListResponse(BaseModel):
    projects: List[ProjectWithAnalysis]
    total: int
    page: int
    per_page: int

class AnalysisStatusResponse(BaseModel):
    status: AnalysisStatus
    progress: int = Field(ge=0, le=100)
    current_agent: Optional[str] = None
    message: Optional[str] = None
