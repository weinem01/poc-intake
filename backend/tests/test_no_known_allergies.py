#!/usr/bin/env python3
"""
Test script specifically for testing the "no known allergies" functionality
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service
from app.core.token_manager import get_charm_api_headers

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def clear_patient_allergies(patient_id: str):
    """Clear all existing allergies for a patient (for testing purposes)"""
    try:
        headers = await get_charm_api_headers()
        
        # First get all existing allergies
        existing_allergies = await ehr_service.get_patient_allergies(patient_id)
        
        if not existing_allergies:
            logger.info("No existing allergies to clear")
            return True
            
        logger.info(f"Found {len(existing_allergies)} existing allergies to clear")
        
        # Delete each allergy
        import httpx
        async with httpx.AsyncClient() as client:
            for allergy in existing_allergies:
                allergy_id = allergy.get("patient_allergy_id")
                if allergy_id:
                    response = await client.delete(
                        f"{ehr_service.base_url}/patients/{patient_id}/allergies/{allergy_id}",
                        headers=headers,
                        timeout=30.0
                    )
                    if response.status_code in [200, 201]:
                        logger.info(f"Deleted allergy: {allergy.get('allergen')}")
                    else:
                        logger.error(f"Failed to delete allergy {allergy_id}: {response.status_code}")
                        
        return True
        
    except Exception as e:
        logger.error(f"Error clearing allergies: {e}")
        return False

async def test_no_known_allergies_clean_patient():
    """Test marking 'no known allergies' on a patient with no existing allergies"""
    try:
        # Use a different patient ID for clean testing
        patient_id = "1043817000084754508"  # You may want to use a test patient
        
        logger.info("\n=== Test 1: No Known Allergies - Clean Patient ===")
        logger.info(f"Patient ID: {patient_id}")
        
        # First, ensure patient has no allergies
        logger.info("Clearing any existing allergies...")
        await clear_patient_allergies(patient_id)
        await asyncio.sleep(1)  # Give API time to process
        
        # Verify patient has no allergies
        existing = await ehr_service.get_patient_allergies(patient_id)
        logger.info(f"Current allergies count: {len(existing)}")
        
        # Now try to mark as "no known allergies"
        headers = await get_charm_api_headers()
        
        # Test data indicating no allergies
        no_allergies_data = [{
            "allergen": "None",
            "reaction": "",
            "severity": ""
        }]
        
        logger.info("Attempting to mark 'no known allergies'...")
        result = await ehr_service._push_allergies_to_charm(
            patient_id,
            no_allergies_data,
            headers
        )
        
        if result:
            logger.info("✅ Successfully marked patient as having no known allergies")
        else:
            logger.error("❌ Failed to mark no known allergies")
            
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

async def test_no_known_allergies_with_existing():
    """Test that we cannot mark 'no known allergies' when patient has existing allergies"""
    try:
        patient_id = "1043817000084754508"
        
        logger.info("\n=== Test 2: No Known Allergies - Patient with Existing Allergies ===")
        logger.info(f"Patient ID: {patient_id}")
        
        # First add an allergy
        headers = await get_charm_api_headers()
        
        test_allergy = [{
            "allergen": "Test Medication",
            "reaction": "Test Reaction",
            "severity": "Mild"
        }]
        
        logger.info("Adding a test allergy first...")
        add_result = await ehr_service._push_allergies_to_charm(
            patient_id,
            test_allergy,
            headers
        )
        
        if add_result:
            logger.info("✅ Test allergy added successfully")
        else:
            logger.error("Failed to add test allergy")
            return False
            
        await asyncio.sleep(1)
        
        # Verify allergy was added
        existing = await ehr_service.get_patient_allergies(patient_id)
        logger.info(f"Current allergies count: {len(existing)}")
        
        # Now try to mark as "no known allergies" (should fail)
        no_allergies_data = [{
            "allergen": "None",
            "reaction": "",
            "severity": ""
        }]
        
        logger.info("Attempting to mark 'no known allergies' (should fail)...")
        result = await ehr_service._push_allergies_to_charm(
            patient_id,
            no_allergies_data,
            headers
        )
        
        if not result:
            logger.info("✅ Correctly prevented marking 'no known allergies' when allergies exist")
            return True
        else:
            logger.error("❌ Incorrectly allowed marking 'no known allergies' with existing allergies")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

async def test_direct_no_known_api():
    """Test the no_known_allergy endpoint directly"""
    try:
        patient_id = "1043817000084754508"
        
        logger.info("\n=== Test 3: Direct No Known Allergy API Test ===")
        logger.info(f"Patient ID: {patient_id}")
        
        # Clear allergies first
        await clear_patient_allergies(patient_id)
        await asyncio.sleep(1)
        
        headers = await get_charm_api_headers()
        
        # Direct API call
        import httpx
        async with httpx.AsyncClient() as client:
            payload = {
                "type": "Medication",
                "status": "No Known"
            }
            
            logger.info(f"Sending payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{ehr_service.base_url}/patients/{patient_id}/no_known_allergy",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
            
            if response.status_code in [200, 201]:
                logger.info("✅ Direct API call successful")
                return True
            else:
                logger.error("❌ Direct API call failed")
                return False
                
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

async def main():
    """Run all no known allergies tests"""
    logger.info("Starting No Known Allergies Tests")
    logger.info("=" * 60)
    
    # Run tests
    tests = [
        ("Clean Patient - No Known Allergies", test_no_known_allergies_clean_patient),
        ("Existing Allergies - Should Prevent No Known", test_no_known_allergies_with_existing),
        ("Direct API Test", test_direct_no_known_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        result = await test_func()
        results.append((test_name, result))
        await asyncio.sleep(2)  # Delay between tests
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, result in results if result)
    logger.info(f"\nTotal: {total_passed}/{len(tests)} tests passed")

if __name__ == "__main__":
    asyncio.run(main())