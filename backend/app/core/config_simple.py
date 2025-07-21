"""Simplified configuration for initial deployment testing"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "production")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "pound-of-cure-dev")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8080"))
    debug: bool = False
    
    # Charm API Configuration
    charm_facility_id: str = "1043817000000046409"
    charm_api_base_url: str = "https://ehr.charmtracker.com/api/ehr/v1"
    
    # CORS
    @property
    def cors_origins(self) -> list[str]:
        env_origins = os.getenv("CORS_ORIGINS")
        if env_origins:
            return env_origins.split(",")
        return ["*"]  # Allow all origins for testing
    
    # Dummy methods to prevent errors during startup
    def get_openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "dummy-key-for-testing")
    
    def get_supabase_url(self) -> str:
        return os.getenv("SUPABASE_URL", "https://dummy.supabase.co")
    
    def get_supabase_service_role_key(self) -> str:
        return os.getenv("SUPABASE_SERVICE_ROLE_KEY", "dummy-key")
    
    def get_charm_client_id(self) -> str:
        return os.getenv("CHARM_CLIENT_ID", "dummy-id")
    
    def get_charm_client_secret(self) -> str:
        return os.getenv("CHARM_CLIENT_SECRET", "dummy-secret")
    
    def get_charm_refresh_token(self) -> str:
        return os.getenv("CHARM_REFRESH_TOKEN", "dummy-token")
    
    def get_charm_api_key(self) -> str:
        return os.getenv("CHARM_API_KEY", "dummy-key")
    
    def get_charm_auth_base_url(self) -> str:
        return os.getenv("CHARM_AUTH_BASE_URL", "https://auth.charmtracker.com")
    
    def get_perplexity_api_key(self) -> str:
        return os.getenv("PERPLEXITY_API_KEY", "dummy-key")

def get_settings() -> Settings:
    return Settings()