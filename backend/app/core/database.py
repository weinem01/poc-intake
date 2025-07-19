"""
Supabase database configuration and connection management
"""

import logging
from typing import Optional

from supabase import create_client, Client
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SupabaseManager:
    """Manages Supabase client connection with lazy initialization"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
        logger.info(f"SupabaseManager initialized for project: {self.settings.gcp_project_id}")
    
    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client"""
        if self._client is None:
            try:
                supabase_url = self.settings.get_supabase_url()
                supabase_key = self.settings.get_supabase_service_role_key()
                
                self._client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        return self._client


# Global instance
supabase_manager = SupabaseManager()


def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return supabase_manager.client