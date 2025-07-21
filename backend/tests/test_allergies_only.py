#!/usr/bin/env python3
"""
Test script specifically for testing the allergies API push
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service
from app.core.token_manager import get_charm_api_headers

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_allergy():
    """Test pushing a single allergy"""
    try:
        patient_id = "1043817000084754508"
        headers = await get_charm_api_headers()
        
        # Test data - single allergy
        allergies = [{
            "allergen": "Penicillin",
            "reaction": "Rash",
            "severity": "Moderate"
        }]
        
        logger.info("=== Testing Single Allergy Push ===")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Allergy data: {json.dumps(allergies, indent=2)}")
        
        # Call the method directly
        result = await ehr_service._push_allergies_to_charm(
            patient_id,
            allergies,
            headers
        )
        
        if result:
            logger.info("✅ Single allergy test PASSED!")
        else:
            logger.error("❌ Single allergy test FAILED!")
            
        return result
        
    except Exception as e:
        logger.error(f"Error during single allergy test: {e}", exc_info=True)
        return False

async def test_multiple_allergies():
    """Test pushing multiple allergies"""
    try:
        patient_id = "1043817000084754508"
        headers = await get_charm_api_headers()
        
        # Test data - multiple allergies
        allergies = [
            {
                "allergen": "Aspirin",
                "reaction": "Hives",
                "severity": "Mild"
            },
            {
                "allergen": "Peanuts",
                "reaction": "Anaphylaxis",
                "severity": "Severe"
            }
        ]
        
        logger.info("\n=== Testing Multiple Allergies Push ===")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Allergies data: {json.dumps(allergies, indent=2)}")
        
        # Call the method directly
        result = await ehr_service._push_allergies_to_charm(
            patient_id,
            allergies,
            headers
        )
        
        if result:
            logger.info("✅ Multiple allergies test PASSED!")
        else:
            logger.error("❌ Multiple allergies test FAILED!")
            
        return result
        
    except Exception as e:
        logger.error(f"Error during multiple allergies test: {e}", exc_info=True)
        return False

async def test_no_known_allergies():
    """Test marking patient as having no known allergies"""
    try:
        patient_id = "1043817000084754508"
        headers = await get_charm_api_headers()
        
        # Test data - no known allergies
        allergies = [{
            "allergen": "None",
            "reaction": "",
            "severity": ""
        }]
        
        logger.info("\n=== Testing No Known Allergies ===")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Allergies data: {json.dumps(allergies, indent=2)}")
        
        # Call the method directly
        result = await ehr_service._push_allergies_to_charm(
            patient_id,
            allergies,
            headers
        )
        
        if result:
            logger.info("✅ No known allergies test PASSED!")
        else:
            logger.error("❌ No known allergies test FAILED!")
            
        return result
        
    except Exception as e:
        logger.error(f"Error during no known allergies test: {e}", exc_info=True)
        return False

async def test_allergy_via_push_intake():
    """Test allergy push through the push_intake_section method"""
    try:
        patient_id = "1043817000084754508"
        
        # Test data matching the intake format
        medical_history_data = {
            "allergies": [
                {
                    "allergen": "Penicillin",
                    "reaction": "Rash",
                    "severity": "Moderate"
                }
            ]
        }
        
        logger.info("\n=== Testing Allergy via push_intake_section ===")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Medical history data: {json.dumps(medical_history_data, indent=2)}")
        
        # Call through push_intake_section
        result = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=medical_history_data
        )
        
        if result:
            logger.info("✅ Push intake section test PASSED!")
        else:
            logger.error("❌ Push intake section test FAILED!")
            
        return result
        
    except Exception as e:
        logger.error(f"Error during push intake section test: {e}", exc_info=True)
        return False

async def main():
    """Run all allergy tests"""
    logger.info("Starting Allergy API Tests")
    logger.info("=" * 60)
    
    # Run tests
    tests = [
        ("Single Allergy", test_single_allergy),
        ("Multiple Allergies", test_multiple_allergies),
        ("No Known Allergies", test_no_known_allergies),
        ("Via Push Intake", test_allergy_via_push_intake)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        result = await test_func()
        results.append((test_name, result))
        await asyncio.sleep(1)  # Small delay between tests
    
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