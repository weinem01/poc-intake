"""
Compare headers and permissions between working GET requests and failing POST requests
"""

import asyncio
import json
import logging
import httpx
from app.core.token_manager import get_charm_api_headers
from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_working_get_vs_failing_post():
    """Compare working GET request with failing POST request"""
    try:
        patient_id = "1043817000084754508"
        settings = get_settings()
        base_url = settings.charm_api_base_url
        headers = await get_charm_api_headers()
        
        logger.info("=== Comparing GET vs POST requests ===")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Headers: {headers}")
        
        async with httpx.AsyncClient() as client:
            # Test 1: Working GET request (we know this works)
            logger.info("\n--- Testing Working GET Request ---")
            get_response = await client.get(
                f"{base_url}/patients/{patient_id}",
                headers=headers,
                timeout=30.0
            )
            logger.info(f"GET Response Status: {get_response.status_code}")
            logger.info(f"GET Response Type: {get_response.headers.get('content-type', 'unknown')}")
            
            # Test 2: Try POST to the same patient endpoint (should fail gracefully)
            logger.info("\n--- Testing POST to Patient Endpoint (should fail but give us info) ---")
            try:
                post_response = await client.post(
                    f"{base_url}/patients/{patient_id}",
                    json={"test": "data"},
                    headers=headers,
                    timeout=30.0
                )
                logger.info(f"POST Response Status: {post_response.status_code}")
                logger.info(f"POST Response: {post_response.text[:500]}")
            except Exception as e:
                logger.info(f"POST Exception: {e}")
            
            # Test 3: Try the simplest possible POST - vitals (which we know worked before)
            logger.info("\n--- Testing POST to Vitals Endpoint (known to work) ---")
            vitals_payload = [{
                "entry_date": "2025-07-20",
                "vitals": [{
                    "vital_name": "Weight",
                    "vital_value": "150",
                    "vital_unit": "lbs"
                }]
            }]
            
            vitals_response = await client.post(
                f"{base_url}/patients/{patient_id}/vitals",
                json=vitals_payload,
                headers=headers,
                timeout=30.0
            )
            logger.info(f"Vitals POST Status: {vitals_response.status_code}")
            logger.info(f"Vitals Response: {vitals_response.text[:500]}")
            
            # Test 4: Check if it's just medical history endpoints
            logger.info("\n--- Testing Medical History Base Endpoint ---")
            try:
                # Try to get existing medical history first
                med_get_response = await client.get(
                    f"{base_url}/patients/{patient_id}/medicalhistory/pastmedicalhistory",
                    headers=headers,
                    timeout=30.0
                )
                logger.info(f"Medical History GET Status: {med_get_response.status_code}")
                logger.info(f"Medical History GET Response: {med_get_response.text[:500]}")
            except Exception as e:
                logger.info(f"Medical History GET Exception: {e}")
                
    except Exception as e:
        logger.error(f"Exception in comparison test: {e}", exc_info=True)

async def test_different_content_types():
    """Test if it's a Content-Type issue"""
    try:
        patient_id = "1043817000084754508"
        settings = get_settings()
        base_url = settings.charm_api_base_url
        base_headers = await get_charm_api_headers()
        
        logger.info("\n=== Testing Different Content-Type Headers ===")
        
        # Test with different content-type headers
        test_headers = [
            {**base_headers, "Content-Type": "application/json"},
            {**base_headers, "Content-Type": "application/json; charset=utf-8"},
            {**base_headers, "content-type": "application/json"},  # lowercase
        ]
        
        simple_payload = {
            "content": "Test medical history",
            "is_html": False
        }
        
        async with httpx.AsyncClient() as client:
            for i, headers in enumerate(test_headers):
                logger.info(f"\n--- Test {i+1}: {headers.get('Content-Type', 'content-type')} ---")
                try:
                    response = await client.post(
                        f"{base_url}/patients/{patient_id}/medicalhistory/pastmedicalhistory",
                        json=simple_payload,
                        headers=headers,
                        timeout=30.0
                    )
                    logger.info(f"Status: {response.status_code}")
                    logger.info(f"Response: {response.text[:200]}")
                except Exception as e:
                    logger.info(f"Exception: {e}")
                    
    except Exception as e:
        logger.error(f"Exception in content-type test: {e}", exc_info=True)

async def run_header_tests():
    """Run all header comparison tests"""
    await test_working_get_vs_failing_post()
    await test_different_content_types()

if __name__ == "__main__":
    asyncio.run(run_header_tests())