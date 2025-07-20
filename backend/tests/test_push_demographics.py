"""
Test the demographics push functionality with provided JSON data
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data provided
test_data = {
    "completed": {
        "isComplete": True,
        "medical_history": {
            "conditions": ["High cholesterol"]
        },
        "appointment_time": "right now",
        "send_email_confirmation": True
    },
    "completed_tracking": {
        "isComplete": True,
        "unasked_fields": [],
        "pushed_to_charm": False
    },
    "intake_demographics": {
        "email": "matthew.weiner@poundofcureweightloss.com",
        "record_id": "POC16872",
        "phone": {
            "home": "",
            "work": "5202983300",
            "mobile": "2488352997",
            "preferred": "mobile",
            "workExtension": ""
        },
        "gender": "male",
        "address": {
            "city": "Tucson",
            "state": "AZ",
            "country": "us",
            "zipCode": "85718",
            "addressLine1": "3010 E Camino Juan Paisano",
            "addressLine2": ""
        },
        "lastName": "patient",
        "firstName": "testing",
        "isComplete": True,
        "middleName": "Jeremy",
        "patient_id": "1043817000084754508",
        "dateOfBirth": "1972-07-28",
        "maritalStatus": "Married",
        "emergencyContact": {
            "name": "Loren Weiner",
            "phone": "2488427542",
            "relationship": "wife"
        },
        "employmentStatus": "Employed",
        "careTeamProviders": [{
            "specialty": "internal medicine",
            "practiceName": "ACP",
            "relationshipType": "Primary Care Physician",
            "isPrimaryCarePhysician": True
        }],
        "communicationPreferences": {
            "preferredMethod": "email",
            "textNotifications": True,
            "emailNotifications": True,
            "voiceNotifications": True
        }
    },
    "intake_demographics_tracking": {
        "isComplete": True,
        "unasked_fields": [],
        "pushed_to_charm": False
    }
}

async def test_push():
    """Test pushing demographics to Charm"""
    try:
        # Extract the patient_id from the demographics data
        demographics_data = test_data["intake_demographics"]
        patient_id = demographics_data.get("patient_id")
        
        if not patient_id:
            logger.error("No patient_id found in demographics data")
            return
            
        logger.info(f"Testing push for patient_id: {patient_id}")
        logger.info("Demographics data to push:")
        logger.info(json.dumps(demographics_data, indent=2))
        
        # Call the push function
        logger.info("\n=== Calling push_intake_section ===")
        success = await ehr_service.push_intake_section(
            section_type="demographics",
            patient_id=patient_id,
            section_data=demographics_data
        )
        
        if success:
            logger.info("✅ Demographics push successful!")
        else:
            logger.error("❌ Demographics push failed!")
            
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_push())