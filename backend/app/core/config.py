"""
Configuration management for POC Intake Application
Handles environment detection and secret management via Google Cloud Secret Manager
"""

import os
import logging
from typing import Dict, Optional
from functools import lru_cache

from google.cloud import secretmanager
from pydantic import BaseModel
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


def get_gcp_project_id() -> str:
    """
    Determine GCP project ID based on environment
    Returns production or development project ID based on deployment context
    """
    # Check for explicit environment variable first
    project_id = os.getenv("GCP_PROJECT_ID")
    if project_id:
        return project_id
    
    # Check for GAE/Cloud Run environment
    gae_service = os.getenv("GAE_SERVICE")
    cloud_run_service = os.getenv("K_SERVICE")
    
    if gae_service or cloud_run_service:
        # In production on Google Cloud
        return "pound-of-cure-llc"
    else:
        # Local development (using gcloud cli auth)
        return "pound-of-cure-dev"


class SecretManager:
    """
    Handles retrieval of secrets from Google Cloud Secret Manager
    Uses lazy loading to prevent startup errors with authentication
    """
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or get_gcp_project_id()
        self._client: Optional[secretmanager.SecretManagerServiceClient] = None
        self._cache: Dict[str, str] = {}
        
        logger.info(f"SecretManager initialized with project_id: {self.project_id}")
    
    @property
    def client(self) -> secretmanager.SecretManagerServiceClient:
        """Lazy initialization of Secret Manager client"""
        if self._client is None:
            try:
                self._client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}")
                raise
        return self._client
    
    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret from Google Secret Manager with caching"""
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode("UTF-8")
            self._cache[secret_name] = secret_value
            logger.debug(f"Retrieved secret: {secret_name}")
            return secret_value
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            raise


# Global secret manager instance (lazy initialization)
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get global secret manager instance with lazy initialization"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


class Settings(BaseSettings):
    """
    Application settings with secret management integration
    All secret properties use lazy evaluation to prevent startup errors
    """
    
    # Environment detection
    environment: str = "development" if get_gcp_project_id() == "pound-of-cure-dev" else "production"
    gcp_project_id: str = get_gcp_project_id()
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = environment == "development"
    
    # Charm API Configuration
    charm_facility_id: str = "1043817000000046409"
    
    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "https://localhost:3000",
        "https://poc-intake-dev.web.app",
        "https://poc-intake.poundofcure.com"
    ]
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("openai-api-key")
    
    def get_supabase_url(self) -> str:
        """Get Supabase URL from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("supabase-url")
    
    def get_supabase_service_role_key(self) -> str:
        """Get Supabase service role key from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("supabase-service-role-key")
    
    def get_charm_client_id(self) -> str:
        """Get Charm Tracker client ID from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("charm-client-id")
    
    def get_charm_client_secret(self) -> str:
        """Get Charm Tracker client secret from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("charm-client-secret")
    
    def get_charm_refresh_token(self) -> str:
        """Get Charm Tracker refresh token from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("charm-refresh-token")
    
    def get_charm_api_key(self) -> str:
        """Get Charm Tracker API key from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("charm-api-key")
    
    def get_charm_auth_base_url(self) -> str:
        """Get Charm Tracker auth base URL from Secret Manager (on-demand)"""
        return get_secret_manager().get_secret("charm-auth-base-url")
    
    @property
    def charm_api_base_url(self) -> str:
        """Get Charm Tracker API base URL (static)"""
        return "https://ehr.charmtracker.com/api/ehr/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


class LogConfig(BaseModel):
    """Logging configuration"""
    
    LOGGER_NAME: str = "poc_intake"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG" if get_gcp_project_id() == "pound-of-cure-dev" else "INFO"
    
    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }