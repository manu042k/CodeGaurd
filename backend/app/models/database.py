from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    github_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    avatar_url = Column(String)
    github_token = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)  # GitHub repo ID
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    description = Column(Text)
    private = Column(Boolean, default=False)
    html_url = Column(String, nullable=False)
    clone_url = Column(String, nullable=False)
    language = Column(String)
    stargazers_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    owner_login = Column(String, nullable=False)
    owner_avatar_url = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    
    # Note: Repository table exists but is not currently linked to projects

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    # Store GitHub repository information directly
    github_repo_id = Column(Integer, nullable=False)  # GitHub repository ID
    github_url = Column(String, nullable=False)       # GitHub repository URL
    github_full_name = Column(String, nullable=False) # e.g., "user/repo"
    status = Column(String, default="never_analyzed")  # never_analyzed, analyzing, completed, failed
    settings = Column(JSON, default=lambda: {
        "analysisConfig": {
            "enabledAgents": ["CodeQuality", "Security", "Architecture", "Documentation"],
            "excludePatterns": ["node_modules", "*.test.*", "dist", "build"],
            "includePaths": ["src", "lib", "pages", "components"]
        },
        "notifications": {
            "onComplete": True,
            "onFailure": True
        }
    })
    analysis_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Integer)  # seconds
    overall_score = Column(Float)
    summary = Column(Text)
    error = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="analyses")
    agent_results = relationship("AgentResult", back_populates="analysis", cascade="all, delete-orphan")

class AgentResult(Base):
    __tablename__ = "agent_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    agent_name = Column(String, nullable=False)  # CodeQuality, Security, Architecture, Documentation
    status = Column(String, default="pending")
    score = Column(Float)
    summary = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Integer)
    error = Column(Text)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="agent_results")
    issues = relationship("Issue", back_populates="agent_result", cascade="all, delete-orphan")

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_result_id = Column(String, ForeignKey("agent_results.id"), nullable=False)
    type = Column(String, nullable=False)  # error, warning, info, suggestion
    severity = Column(String, nullable=False)  # critical, high, medium, low
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String)
    line_number = Column(Integer)
    column_number = Column(Integer)
    rule = Column(String)
    
    # Relationships
    agent_result = relationship("AgentResult", back_populates="issues")
