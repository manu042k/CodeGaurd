from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.auth import create_access_token, verify_token
from app.models.database import User
from app.models.schemas import User as UserSchema
from app.services.github_service import GitHubService
from datetime import timedelta
import requests
import secrets
from typing import Optional

router = APIRouter()
security = HTTPBearer()

# In-memory state storage (in production, use Redis)
auth_states = {}

@router.get("/github/login")
async def github_login():
    """Initiate GitHub OAuth flow"""
    state = secrets.token_urlsafe(32)
    auth_states[state] = True  # Store state for validation
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri=http://localhost:3000/api/auth/github/callback&"
        f"scope=user:email,repo&"
        f"state={state}"
    )
    
    return {"auth_url": github_auth_url, "state": state}

@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
    # Validate state
    if state not in auth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )
    
    # Remove used state
    del auth_states[state]
    
    try:
        # Exchange code for access token
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received"
            )
        
        # Get user info from GitHub
        github_service = GitHubService(access_token)
        github_user = github_service.get_user()
        
        if not github_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from GitHub"
            )
        
        # Find or create user
        user = db.query(User).filter(User.github_id == str(github_user["id"])).first()
        
        if not user:
            # Create new user
            user = User(
                github_id=str(github_user["id"]),
                username=github_user["login"],
                email=github_user.get("email", ""),
                full_name=github_user.get("name", ""),
                avatar_url=github_user.get("avatar_url", ""),
                github_token=access_token
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.username = github_user["login"]
            user.email = github_user.get("email", user.email)
            user.full_name = github_user.get("name", user.full_name)
            user.avatar_url = github_user.get("avatar_url", user.avatar_url)
            user.github_token = access_token
            db.commit()
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/auth/callback?token={jwt_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=UserSchema)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    user_id = verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/logout")
async def logout():
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify if token is valid"""
    user_id = verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"valid": True, "user_id": user_id}

@router.get("/test-db")
async def test_database_connection(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        # Simple query to test database
        user_count = db.query(User).count()
        return {"status": "ok", "user_count": user_count}
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )

@router.post("/sync-user")
async def sync_user_from_frontend(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """Sync user data from NextAuth frontend"""
    try:
        print(f"🔄 Syncing user data: {user_data}")
        
        github_id = user_data.get("github_id")
        if not github_id:
            print("❌ No GitHub ID provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub ID is required"
            )
        
        print(f"🔍 Looking for user with GitHub ID: {github_id}")
        
        # Find or create user
        user = db.query(User).filter(User.github_id == str(github_id)).first()
        
        if not user:
            print("👤 Creating new user...")
            # Create new user
            user = User(
                github_id=str(github_id),
                username=user_data.get("username") or "",
                email=user_data.get("email") or "",
                full_name=user_data.get("full_name"),
                avatar_url=user_data.get("avatar_url"),
                github_token=user_data.get("github_token") or ""
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created user: {user.id}")
        else:
            print(f"🔄 Updating existing user: {user.id}")
            # Update existing user
            user.username = user_data.get("username") or user.username
            user.email = user_data.get("email") or user.email
            user.full_name = user_data.get("full_name") or user.full_name
            user.avatar_url = user_data.get("avatar_url") or user.avatar_url
            user.github_token = user_data.get("github_token") or user.github_token
            db.commit()
            print("✅ Updated user")
        
        print("🎫 Creating JWT token...")
        # Create JWT token for backend API access
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        response_data = {
            "id": user.id,
            "github_id": user.github_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "jwt_token": jwt_token
        }
        
        print(f"✅ User sync successful: {user.username}")
        return response_data
        
    except Exception as e:
        import traceback
        error_msg = f"User sync failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

# Dependency to get current user
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    user_id = verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
