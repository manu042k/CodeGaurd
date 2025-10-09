from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    github_repo_id: int
    github_url: str
    github_full_name: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Project(ProjectBase):
    id: str
    user_id: str
    github_repo_id: int
    github_url: str
    github_full_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# For backwards compatibility, keep ProjectWithAnalysis as an alias to Project
class ProjectWithAnalysis(Project):
    pass
