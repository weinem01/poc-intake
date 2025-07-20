"""
Test specific medical history APIs with exact payload formats
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

async def test_allergy_api():
    """Test the allergy API with exact format"""
    try:
        patient_id = "1043817000084754508"
        settings = get_settings()
        base_url = settings.charm_api_base_url
        headers = await get_charm_api_headers()
        
        logger.info("=== Testing Allergy API ===")
        
        # Test payload exactly as specified in the API docs
        allergy_payload = [
            {
                "allergen": "Penicillin",
                "allergy_type": "Drug", 
                "severity": "Moderate",
                "reactions": "Rash",
                "is_active": True,
                "comments": ""
            }
        ]
        
        logger.info(f"URL: {base_url}/patients/{patient_id}/allergies")
        logger.info(f"Payload: {json.dumps(allergy_payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/patients/{patient_id}/allergies",
                json=allergy_payload,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            response_text = response.text
            logger.info(f"Response: {response_text}")
            
            if response.status_code in [200, 201]:
                logger.info("✅ Allergy API working!")
                return True
            else:
                logger.error(f"❌ Allergy API failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception in allergy API test: {e}", exc_info=True)
        return False

async def test_medication_api():
    """Test the medication API with exact format"""
    try:
        patient_id = "1043817000084754508"
        settings = get_settings()
        base_url = settings.charm_api_base_url
        headers = await get_charm_api_headers()
        
        logger.info("=== Testing Medication API ===")
        
        # Test payload exactly as specified in the updated API docs
        medication_payload = [
            {
                "drug_name": "Lisinopril",
                "strength_description": "10mg",
                "directions": "Take 1 tablet daily",
                "is_active": True,
                "is_custom_drug": True,
                "dispense": 30.0,
                "refills": "0",
                "substitute_generic": True,
                "manufacturing_type": "Manufactured"
            }
        ]
        
        logger.info(f"URL: {base_url}/patients/{patient_id}/medications")
        logger.info(f"Payload: {json.dumps(medication_payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/patients/{patient_id}/medications",
                json=medication_payload,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            response_text = response.text
            logger.info(f"Response: {response_text}")
            
            if response.status_code in [200, 201]:
                logger.info("✅ Medication API working!")
                return True
            else:
                logger.error(f"❌ Medication API failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception in medication API test: {e}", exc_info=True)
        return False

async def test_past_medical_history_api():
    """Test the past medical history API"""
    try:
        patient_id = "1043817000084754508"
        settings = get_settings()
        base_url = settings.charm_api_base_url
        headers = await get_charm_api_headers()
        
        logger.info("=== Testing Past Medical History API ===")
        
        # Simple past medical history payload
        pmhx_payload = {
            "content": "Past Medical History:\n• Hypertension\n• Diabetes Type 2",
            "is_html": False
        }
        
        logger.info(f"URL: {base_url}/patients/{patient_id}/medicalhistory/pastmedicalhistory")
        logger.info(f"Payload: {json.dumps(pmhx_payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/patients/{patient_id}/medicalhistory/pastmedicalhistory",
                json=pmhx_payload,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            response_text = response.text
            logger.info(f"Response: {response_text}")
            
            if response.status_code in [200, 201]:
                logger.info("✅ Past Medical History API working!")
                return True
            else:
                logger.error(f"❌ Past Medical History API failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception in past medical history API test: {e}", exc_info=True)
        return False

async def run_specific_tests():
    """Run tests for specific medical APIs"""
    logger.info("Testing specific medical history APIs...")
    
    # Test each API individually
    results = []
    
    logger.info("\n" + "="*50)
    allergy_result = await test_allergy_api()
    results.append(("Allergy API", allergy_result))
    
    logger.info("\n" + "="*50)
    medication_result = await test_medication_api()
    results.append(("Medication API", medication_result))
    
    logger.info("\n" + "="*50)
    pmhx_result = await test_past_medical_history_api()
    results.append(("Past Medical History API", pmhx_result))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("SUMMARY:")
    for api_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{api_name}: {status}")

if __name__ == "__main__":
    asyncio.run(run_specific_tests())