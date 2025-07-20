"""
Most basic test to verify Charm API connectivity and authentication
"""

import asyncio
import logging
import httpx
from app.core.token_manager import get_charm_api_headers
from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_auth():
    """Test if we can get auth headers"""
    try:
        logger.info("=== Testing Basic Authentication ===")
        headers = await get_charm_api_headers()
        logger.info(f"Auth headers obtained: {list(headers.keys())}")
        return headers
    except Exception as e:
        logger.error(f"Failed to get auth headers: {e}", exc_info=True)
        return None

async def test_patient_details_api(patient_id: str, headers):
    """Test the simplest API call - get patient details (known to work)"""
    try:
        settings = get_settings()
        base_url = settings.charm_api_base_url
        
        logger.info(f"=== Testing Patient Details API ===")
        logger.info(f"URL: {base_url}/patients/{patient_id}")
        logger.info(f"Headers: {headers}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/patients/{patient_id}",
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            # Log first 500 chars of response to see if it's HTML or JSON
            response_text = response.text
            logger.info(f"Response Length: {len(response_text)} characters")
            logger.info(f"Response Preview (first 500 chars): {response_text[:500]}")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    logger.info("✅ Successfully got JSON response")
                    logger.info(f"Patient data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
                    return True
                except Exception as json_error:
                    logger.error(f"❌ Got 200 but failed to parse JSON: {json_error}")
                    return False
            else:
                logger.error(f"❌ API call failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception during API call: {e}", exc_info=True)
        return False

async def test_patients_list_api(headers):
    """Test the patients list API that we know works from previous tests"""
    try:
        settings = get_settings()
        base_url = settings.charm_api_base_url
        
        logger.info(f"=== Testing Patients List API ===")
        logger.info(f"URL: {base_url}/patients")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/patients",
                params={
                    "record_id": "12345",  # Test record ID
                    "facility_id": "ALL"
                },
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            response_text = response.text
            logger.info(f"Response Preview: {response_text[:500]}")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    logger.info("✅ Patients list API working")
                    return True
                except:
                    logger.error("❌ Patients list returned HTML instead of JSON")
                    return False
            else:
                logger.error(f"❌ Patients list API failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception during patients list API: {e}", exc_info=True)
        return False

async def run_basic_tests():
    """Run the most basic connectivity tests"""
    logger.info("Starting basic API connectivity tests...")
    
    # Test 1: Can we get auth headers?
    headers = await test_basic_auth()
    if not headers:
        logger.error("❌ Cannot get authentication headers - stopping tests")
        return
    
    # Test 2: Can we call the patients list API?
    list_success = await test_patients_list_api(headers)
    if not list_success:
        logger.error("❌ Basic patients list API failed - there may be auth or connectivity issues")
        return
    
    # Test 3: Can we get details for a specific patient?
    patient_id = "1043817000084754508"  # Known working patient ID
    details_success = await test_patient_details_api(patient_id, headers)
    
    if details_success:
        logger.info("✅ All basic tests passed! API connectivity is working")
    else:
        logger.error("❌ Patient details API failed")

if __name__ == "__main__":
    asyncio.run(run_basic_tests())