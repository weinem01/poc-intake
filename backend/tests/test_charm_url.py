"""
Quick test to check the Charm auth URL
"""

from app.core.config import get_settings

settings = get_settings()

try:
    auth_url = settings.get_charm_auth_base_url()
    print(f"Charm Auth Base URL: {auth_url}")
    print(f"Token endpoint would be: {auth_url}/oauth/v2/token")
except Exception as e:
    print(f"Error: {e}")