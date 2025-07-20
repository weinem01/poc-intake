"""
Simple test script to test individual medical history APIs one at a time
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_allergies_only():
    """Test only the allergy API"""
    try:
        patient_id = "1043817000084754508"
        
        allergies_data = {
            "allergies": [
                {
                    "allergen": "Penicillin", 
                    "reaction": "Rash",
                    "severity": "Moderate"
                }
            ]
        }
        
        logger.info("=== Testing Allergies API Only ===")
        logger.info(f"Data: {json.dumps(allergies_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=allergies_data
        )
        
        if success:
            logger.info("✅ Allergies test successful!")
        else:
            logger.error("❌ Allergies test failed!")
            
    except Exception as e:
        logger.error(f"Error during allergies test: {e}", exc_info=True)

async def test_medications_only():
    """Test only the medication API"""
    try:
        patient_id = "1043817000084754508"
        
        medications_data = {
            "currentMedications": [
                {
                    "medicationName": "Lisinopril",
                    "strength": "10mg",
                    "directions": "Take 1 tablet daily"
                }
            ]
        }
        
        logger.info("=== Testing Medications API Only ===")
        logger.info(f"Data: {json.dumps(medications_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=medications_data
        )
        
        if success:
            logger.info("✅ Medications test successful!")
        else:
            logger.error("❌ Medications test failed!")
            
    except Exception as e:
        logger.error(f"Error during medications test: {e}", exc_info=True)

async def test_past_medical_history_only():
    """Test only the past medical history API"""
    try:
        patient_id = "1043817000084754508"
        
        pmhx_data = {
            "PMHx": ["Hypertension", "Diabetes Type 2"]
        }
        
        logger.info("=== Testing Past Medical History API Only ===")
        logger.info(f"Data: {json.dumps(pmhx_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=pmhx_data
        )
        
        if success:
            logger.info("✅ Past Medical History test successful!")
        else:
            logger.error("❌ Past Medical History test failed!")
            
    except Exception as e:
        logger.error(f"Error during past medical history test: {e}", exc_info=True)

if __name__ == "__main__":
    async def run_simple_tests():
        await test_allergies_only()
        await test_medications_only() 
        await test_past_medical_history_only()
    
    asyncio.run(run_simple_tests())