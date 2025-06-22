from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from fastapi import HTTPException, status
import jwt
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class KeycloakManager:
    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
            verify=True
        )
        self._public_key = None

    async def get_public_key(self) -> str:
        """Get Keycloak public key for JWT verification"""
        if not self._public_key:
            try:
                # Get the raw public key
                raw_public_key = self.keycloak_openid.public_key()
                # Format it as PEM certificate
                self._public_key = f"-----BEGIN PUBLIC KEY-----\n{raw_public_key}\n-----END PUBLIC KEY-----"
            except KeycloakError as e:
                logger.error(f"Error getting Keycloak public key: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
        return self._public_key

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Keycloak and return tokens"""
        try:
            token = self.keycloak_openid.token(username, password)
            return token
        except KeycloakError as e:
            logger.error(f"Keycloak authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with Keycloak"""
        try:
            public_key = await self.get_public_key()
            options = {"verify_signature": True, "verify_aud": False, "exp": True}
            
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options=options
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except KeycloakError as e:
            logger.error(f"Keycloak token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            token = self.keycloak_openid.refresh_token(refresh_token)
            return token
        except KeycloakError as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by invalidating refresh token"""
        try:
            self.keycloak_openid.logout(refresh_token)
            return True
        except KeycloakError as e:
            logger.error(f"Logout error: {e}")
            return False

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user information from Keycloak"""
        try:
            user_info = self.keycloak_openid.userinfo(token)
            return user_info
        except KeycloakError as e:
            logger.error(f"Error getting user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register new user in Keycloak (requires admin token)"""
        try:
            # This would require admin access - implement based on your needs
            # For now, we'll return a placeholder
            return {"message": "User registration not implemented yet"}
        except Exception as e:
            logger.error(f"User registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )


# Global instance
keycloak_manager = KeycloakManager()