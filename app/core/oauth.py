import logging
from typing import Optional, Dict, Any

import httpx
from authlib.integrations.starlette_client import OAuth
from jose import jwt
from starlette.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class OAuthManager:
    """Manage OAuth providers."""

    def __init__(self):
        self.config = Config(".env")
        self.oauth = OAuth(self.config)
        self._setup_providers()

    def _setup_providers(self):
        """Setup OAuth providers."""
        # Google OAuth
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name="google",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
                client_kwargs={"scope": "openid email profile"},
            )

        # Apple OAuth (Sign in with Apple)
        # if all([settings.APPLE_CLIENT_ID, settings.APPLE_KEY_ID,
        #         settings.APPLE_TEAM_ID, settings.APPLE_PRIVATE_KEY_PATH]):
        #     self.oauth.register(
        #         name='apple',
        #         client_id=settings.APPLE_CLIENT_ID,
        #         client_secret=self._generate_apple_client_secret(),
        #         authorize_url='https://appleid.apple.com/auth/authorize',
        #         access_token_url='https://appleid.apple.com/auth/token',
        #         client_kwargs={'scope': 'name email'}
        #     )

    # def _generate_apple_client_secret(self) -> str:
    #     """Generate Apple client secret JWT."""
    #     try:
    #         with open(settings.APPLE_PRIVATE_KEY_PATH, 'rb') as key_file:
    #             private_key = serialization.load_pem_private_key(
    #                 key_file.read(), password=None
    #             )

    #         headers = {
    #             'kid': settings.APPLE_KEY_ID,
    #             'alg': 'ES256'
    #         }

    #         payload = {
    #             'iss': settings.APPLE_TEAM_ID,
    #             'iat': int(time.time()),
    #             'exp': int(time.time()) + 86400,  # 1 day
    #             'aud': 'https://appleid.apple.com',
    #             'sub': settings.APPLE_CLIENT_ID
    #         }

    #         return jose_jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    #     except Exception as e:
    #         print(f"Error generating Apple client secret: {e}")
    #         return ""

    async def get_user_info(
        self, provider: str, token: str
    ) -> Optional[Dict[str, Any]]:
        """Get user info from OAuth provider."""
        if provider == "google":
            return await self._get_google_user_info(token)
        elif provider == "apple":
            return await self._get_apple_user_info(token)
        return None

    async def _get_google_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Google."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error getting Google user info: {e}")
        return None

    async def _get_apple_user_info(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Apple ID token. Note: Signature verification is skipped!"""
        try:
            # Apple returns user info in the ID token
            decoded = jwt.decode(id_token, key="", options={"verify_signature": False})
            return {
                "id": decoded.get("sub"),
                "email": decoded.get("email"),
                "name": decoded.get("name", ""),
                "email_verified": decoded.get("email_verified", False),
            }
        except Exception as e:
            logger.error(f"Error decoding Apple ID token: {e}")
        return None


# Global OAuth manager
oauth_manager = OAuthManager()
