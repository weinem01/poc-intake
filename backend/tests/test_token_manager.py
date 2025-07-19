"""
Test script to verify Charm Token Manager functionality
"""

import asyncio
import logging
from app.core.token_manager import charm_token_manager, get_charm_api_headers

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_token_manager():
    """Test the token manager functionality"""
    print("=== Testing Charm Token Manager ===\n")
    
    try:
        # Test 1: Check if secrets can be accessed
        print("1. Testing secret access...")
        try:
            client_id = charm_token_manager.client_id
            print(f"   ✓ Client ID retrieved: {client_id[:10]}..." if client_id else "   ✗ No client ID")
        except Exception as e:
            print(f"   ✗ Error getting client ID: {e}")
            return
        
        # Test 2: Get access token
        print("\n2. Testing token refresh...")
        try:
            token = await charm_token_manager.get_token()
            print(f"   ✓ Access token retrieved: {token[:20]}..." if token else "   ✗ No token")
            print(f"   ✓ Token expires at: {charm_token_manager.expires_at}")
        except Exception as e:
            print(f"   ✗ Error getting token: {e}")
            return
        
        # Test 3: Get API headers
        print("\n3. Testing API headers generation...")
        try:
            headers = await get_charm_api_headers()
            print("   ✓ Headers generated:")
            for key, value in headers.items():
                if key == "Authorization":
                    print(f"     - {key}: Bearer {value[7:27]}...")
                elif key == "api_key":
                    print(f"     - {key}: {value[:20]}...")
                else:
                    print(f"     - {key}: {value}")
        except Exception as e:
            print(f"   ✗ Error getting headers: {e}")
            return
        
        # Test 4: Test token refresh
        print("\n4. Testing forced token refresh...")
        try:
            new_token = await charm_token_manager.get_token(force_new_token=True)
            print(f"   ✓ New token retrieved: {new_token[:20]}...")
            print(f"   ✓ New expiration: {charm_token_manager.expires_at}")
        except Exception as e:
            print(f"   ✗ Error refreshing token: {e}")
            return
        
        # Test 5: Start background refresh
        print("\n5. Testing background refresh start...")
        try:
            await charm_token_manager.start_background_refresh()
            print("   ✓ Background refresh started")
            
            # Wait a bit to see if it's working
            await asyncio.sleep(2)
            
            # Stop it
            await charm_token_manager.stop()
            print("   ✓ Background refresh stopped")
        except Exception as e:
            print(f"   ✗ Error with background refresh: {e}")
        
        print("\n=== All tests completed ===")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Make sure you have authenticated with gcloud:")
    print("  gcloud auth application-default login\n")
    
    asyncio.run(test_token_manager())