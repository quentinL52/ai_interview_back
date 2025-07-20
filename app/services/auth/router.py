from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.schemas.auth_schemas import Token, AuthResponse, TokenValidationRequest, TokenValidationResponse
from app.services.auth import service
from app.services.auth.oauth_service import oauth_service
from app.services.auth.security import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from app.config import settings
import urllib.parse
import json

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Route existante (gardée pour compatibilité)
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user = await service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Nouvelles routes OAuth
@router.get("/oauth/{provider}")
async def oauth_redirect(provider: str):
    """Initie l'authentification OAuth"""
    if provider == "google":
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(settings.GOOGLE_REDIRECT_URI)}&"
            "scope=openid email profile&"
            "response_type=code&"
            "access_type=offline"
        )
        return RedirectResponse(google_auth_url)
    
    raise HTTPException(status_code=400, detail="Provider not supported")

@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str, 
    code: str = None, 
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Gère le callback OAuth"""
    if error:
        error_url = f"{settings.FRONTEND_ERROR_URL}?error={error}"
        return RedirectResponse(error_url)
    
    if not code:
        error_url = f"{settings.FRONTEND_ERROR_URL}?error=no_code"
        return RedirectResponse(error_url)
    
    try:
        auth_result = await oauth_service.authenticate_user(provider, code, db)
        
        # Créer l'URL de succès avec le token
        success_url = (
            f"{settings.FRONTEND_SUCCESS_URL}?"
            f"token={auth_result['access_token']}&"
            f"user={urllib.parse.quote(json.dumps(auth_result['user']))}"
        )
        return RedirectResponse(success_url)
        
    except Exception as e:
        print(f"OAuth callback error: {e}")  # Log pour debug
        error_url = f"{settings.FRONTEND_ERROR_URL}?error=auth_failed"
        return RedirectResponse(error_url)

@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    request: TokenValidationRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Valide un token JWT"""
    try:
        user = await get_current_user(request.token, db)
        
        return TokenValidationResponse(
            valid=True,
            user={
                "id": user.id,
                "email": user.email,
                "name": getattr(user, 'name', user.email.split('@')[0]),
                "picture_url": getattr(user, 'picture_url', None),
                "google_id": getattr(user, 'google_id', None),
                "candidate_mongo_id": getattr(user, 'candidate_mongo_id', None),
                "is_active": getattr(user, 'is_active', True),
                "created_at": getattr(user, 'created_at', None)
            }
        )
    except Exception as e:
        print(f"Token validation error: {e}")
        return TokenValidationResponse(valid=False, user=None)