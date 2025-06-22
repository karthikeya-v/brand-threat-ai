from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.keycloak import keycloak_manager

router = APIRouter()
security = HTTPBearer()


class KeycloakLogin(BaseModel):
    username: str
    password: str


class KeycloakToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    sub: str
    email: str
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None


@router.post("/keycloak/login", response_model=KeycloakToken)
async def keycloak_login(credentials: KeycloakLogin):
    """Login with Keycloak credentials"""
    token_data = await keycloak_manager.authenticate_user(
        credentials.username, 
        credentials.password
    )
    
    return KeycloakToken(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_in=token_data["expires_in"]
    )


@router.post("/keycloak/refresh", response_model=KeycloakToken)
async def refresh_keycloak_token(token_data: TokenRefresh):
    """Refresh Keycloak access token"""
    refreshed_token = await keycloak_manager.refresh_token(token_data.refresh_token)
    
    return KeycloakToken(
        access_token=refreshed_token["access_token"],
        refresh_token=refreshed_token["refresh_token"],
        expires_in=refreshed_token["expires_in"]
    )


@router.post("/keycloak/logout")
async def keycloak_logout(token_data: TokenRefresh):
    """Logout from Keycloak"""
    success = await keycloak_manager.logout_user(token_data.refresh_token)
    
    if success:
        return {"message": "Successfully logged out"}
    else:
        return {"message": "Logout completed (token may have been already invalid)"}


@router.get("/keycloak/me", response_model=UserInfo)
async def get_keycloak_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user information from Keycloak"""
    token = credentials.credentials
    user_info = await keycloak_manager.get_user_info(token)
    
    return UserInfo(
        sub=user_info.get("sub"),
        email=user_info.get("email"),
        name=user_info.get("name"),
        preferred_username=user_info.get("preferred_username"),
        given_name=user_info.get("given_name"),
        family_name=user_info.get("family_name")
    )


@router.get("/keycloak/verify")
async def verify_keycloak_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify Keycloak JWT token"""
    token = credentials.credentials
    decoded_token = await keycloak_manager.verify_token(token)
    
    return {
        "valid": True,
        "user_id": decoded_token.get("sub"),
        "username": decoded_token.get("preferred_username"),
        "email": decoded_token.get("email"),
        "exp": decoded_token.get("exp")
    }


async def get_current_keycloak_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current user from Keycloak token"""
    token = credentials.credentials
    decoded_token = await keycloak_manager.verify_token(token)
    return decoded_token


# Export the dependency for use in other routes
__all__ = ["router", "get_current_keycloak_user"]