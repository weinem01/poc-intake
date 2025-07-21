"""
Charm Tracker API Token Manager
Uses Supabase authTokens table for token storage and automatic refresh
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from app.core.database import get_supabase_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CharmTokenManager:
    """Manages Charm Tracker API authentication tokens with Supabase storage"""

    def __init__(self):
        self.settings = get_settings()
        self.table_name = "authTokens"
        logger.info("CharmTokenManager initialized with Supabase storage")

    def _get_supabase_client(self):
        """Get Supabase client"""
        return get_supabase_client()

    def _get_secret(self, secret_name: str) -> str:
        """Get secret from settings (which handles Secret Manager)"""
        if secret_name == "charm-client-id":
            return self.settings.get_charm_client_id()
        elif secret_name == "charm-client-secret":
            return self.settings.get_charm_client_secret()
        elif secret_name == "charm-refresh-token":
            return self.settings.get_charm_refresh_token()
        elif secret_name == "charm-api-key":
            return self.settings.get_charm_api_key()
        else:
            raise ValueError(f"Unknown secret: {secret_name}")

    async def _get_token_from_db(self) -> Optional[Dict]:
        """Get charm token from Supabase authTokens table"""
        try:
            response = self._get_supabase_client().table(self.table_name).select("*").eq("tokenName", "charm").execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving charm token from database: {e}")
            raise

    async def _save_token_to_db(self, access_token: str, expires_in: int) -> None:
        """Save/update charm token in Supabase authTokens table"""
        try:
            # Calculate expiration datetime
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            token_data = {
                "tokenName": "charm",
                "authToken": access_token,
                "tokenExpiration": expires_at.isoformat()
            }
            
            # Try to update existing record first
            response = self._get_supabase_client().table(self.table_name).update(token_data).eq("tokenName", "charm").execute()
            
            # If no rows were updated, insert new record
            if not response.data:
                response = self._get_supabase_client().table(self.table_name).insert(token_data).execute()
            
            logger.info(f"Saved charm token to database, expires at {expires_at}")
            
        except Exception as e:
            logger.error(f"Error saving charm token to database: {e}")
            raise

    async def _refresh_token(self) -> str:
        """Refresh the access token using the refresh token"""
        try:
            # Get credentials from Secret Manager
            refresh_token = self._get_secret("charm-refresh-token")
            client_id = self._get_secret("charm-client-id")
            client_secret = self._get_secret("charm-client-secret")
            
            # Build the token refresh URL
            access_token_url = (
                f"https://accounts.charmtracker.com/oauth/v2/token"
                f"?refresh_token={refresh_token}"
                f"&client_id={client_id}"
                f"&client_secret={client_secret}"
                f"&grant_type=refresh_token"
            )
            
            headers = {"Cache-Control": "no-cache"}
            
            logger.info("Refreshing Charm Tracker access token")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(access_token_url, headers=headers)
                
                if response.status_code == 400:
                    logger.error(f"Token refresh failed with 400 - refresh token may be expired: {response.text}")
                    raise ValueError("Refresh token is invalid or expired. Manual re-authentication required.")
                
                response.raise_for_status()
                auth_data = response.json()
                
                access_token = auth_data.get("access_token")
                if not access_token:
                    raise ValueError("No access_token in response")
                
                expires_in = auth_data.get("expires_in", 3600)  # Default to 1 hour
                
                # Save to database
                await self._save_token_to_db(access_token, expires_in)
                
                logger.info("Token refreshed and saved successfully")
                return access_token
                
        except Exception as e:
            logger.error(f"Failed to refresh Charm Tracker token: {e}")
            raise

    async def get_token(self) -> str:
        """Get current valid access token, refreshing if necessary"""
        #print("DEBUG: get_token called")
        try:
            #print("DEBUG: About to get token from database")
            # Get token from database
            token_record = await self._get_token_from_db()
            #print(f"DEBUG: Got token record: {token_record}")
            
            if token_record:
                # Check if token is still valid
                expiration_str = token_record.get("tokenExpiration")
                if expiration_str:
                    # Parse expiration time
                    expiration_time = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
                    if isinstance(expiration_time.tzinfo, type(None)):
                        # Assume UTC if no timezone info
                        expiration_time = expiration_time.replace(tzinfo=None)
                        current_time = datetime.utcnow()
                    else:
                        current_time = datetime.now(expiration_time.tzinfo)
                    
                    # Check if token is still valid (with 1 minute buffer)
                    if current_time < (expiration_time - timedelta(minutes=1)):
                        logger.debug("Using existing valid token from database")
                        return token_record["authToken"]
            
            # Token is expired or doesn't exist, refresh it
            logger.info("Token expired or not found, refreshing...")
            return await self._refresh_token()
            
        except Exception as e:
            logger.error(f"Error getting charm token: {e}")
            raise

    async def get_api_headers(self) -> Dict[str, str]:
        """Get complete API headers for Charm Tracker requests"""
        try:
            access_token = await self.get_token()
            api_key = self._get_secret("charm-api-key")
            
            return {
                "api_key": api_key,
                "Authorization": f"Bearer {access_token}",
                "Cache-Control": "no-cache",
            }
            
        except Exception as e:
            logger.error(f"Error getting API headers: {e}")
            raise


# Global instance
charm_token_manager = CharmTokenManager()


async def get_charm_api_headers() -> Dict[str, str]:
    """FastAPI dependency to get Charm Tracker API headers"""
    return await charm_token_manager.get_api_headers()