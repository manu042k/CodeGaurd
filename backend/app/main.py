from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import projects, github, auth, analysis, repository_analysis
from app.core.database import engine
from app.models.database import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "CodeGuard API is running"}

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(github.router, prefix=f"{settings.API_V1_STR}/github", tags=["github"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}/analyses", tags=["analyses"])
app.include_router(repository_analysis.router, prefix=f"{settings.API_V1_STR}/repository-analysis", tags=["repository-analysis"])

@app.get("/")
async def root():
    return {"message": "CodeGuard API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
