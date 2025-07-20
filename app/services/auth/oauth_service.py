from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.postgres.user_model import User
from app.services.auth.service import create_access_token
from app.config import settings
from datetime import datetime
import httpx
import json

class AuthProvider(ABC):
    """Interface pour les fournisseurs d'authentification"""
    
    @abstractmethod
    async def get_user_info(self, code: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass

class GoogleAuthProvider(AuthProvider):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    async def get_user_info(self, code: str) -> Dict[str, Any]:
        # Échanger le code contre un token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Récupérer les infos utilisateur
            user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={tokens['access_token']}"
            user_response = await client.get(user_info_url)
            user_response.raise_for_status()
            
            return user_response.json()
    
    def get_provider_name(self) -> str:
        return "google"

class OAuthService:
    def __init__(self):
        self.providers = {
            "google": GoogleAuthProvider(
                settings.GOOGLE_CLIENT_ID,
                settings.GOOGLE_CLIENT_SECRET,
                settings.GOOGLE_REDIRECT_URI
            )
        }
    
    async def authenticate_user(self, provider: str, code: str, db: AsyncSession) -> Dict[str, Any]:
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not supported")
        
        auth_provider = self.providers[provider]
        user_info = await auth_provider.get_user_info(code)
        
        # Chercher ou créer l'utilisateur
        user = await self.get_or_create_user(user_info, provider, db)
        
        # Créer le token JWT
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture_url": user.picture_url
            }
        }
    
    async def get_or_create_user(self, user_info: Dict, provider: str, db: AsyncSession) -> User:
        if provider == "google":
            return await self._handle_google_user(user_info, db)
        
        raise ValueError(f"Provider {provider} not implemented")
    
    async def _handle_google_user(self, user_info: Dict, db: AsyncSession) -> User:
        # Chercher par google_id ou email
        query = select(User).where(
            or_(
                User.google_id == user_info["id"],
                User.email == user_info["email"]
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # Mettre à jour les infos si nécessaire
            if not user.google_id:
                user.google_id = user_info["id"]
            if user.auth_providers is None:
                user.auth_providers = []
            if "google" not in user.auth_providers:
                user.auth_providers = user.auth_providers + ["google"]
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Mettre à jour le nom et photo si vides ou différents
            if not user.name or user.name != user_info["name"]:
                user.name = user_info["name"]
            if not user.picture_url or user.picture_url != user_info.get("picture"):
                user.picture_url = user_info.get("picture")
        else:
            # Créer nouvel utilisateur
            user = User(
                email=user_info["email"],
                name=user_info["name"],
                picture_url=user_info.get("picture"),
                google_id=user_info["id"],
                auth_providers=["google"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                candidate_mongo_id=None
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        return user

oauth_service = OAuthService()