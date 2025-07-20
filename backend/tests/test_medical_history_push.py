"""
Test script to push medical history data including medications, allergies, past medical history, social history, family history, and past surgeries
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data representing a complete medical history
test_medical_history_data = {
    "isComplete": True,
    "currentMedications": [
        {
            "medicationName": "Lisinopril",
            "strength": "10mg",
            "directions": "Take 1 tablet by mouth daily"
        },
        {
            "medicationName": "Metformin",
            "strength": "500mg",
            "directions": "Take 1 tablet by mouth twice daily with meals"
        },
        {
            "medicationName": "Atorvastatin",
            "strength": "20mg",
            "directions": "Take 1 tablet by mouth at bedtime"
        }
    ],
    "allergies": [
        {
            "allergen": "Penicillin",
            "reaction": "Rash, hives",
            "severity": "Moderate"
        },
        {
            "allergen": "Shellfish",
            "reaction": "Swelling, difficulty breathing",
            "severity": "Severe"
        }
    ],
    "PMHx": [
        "Hypertension",
        "Type 2 Diabetes Mellitus",
        "Hyperlipidemia"
    ],
    "PMHxObesityComorbid": [
        "Sleep apnea",
        "Osteoarthritis of knees",
        "GERD"
    ],
    "familyHistory": [
        {
            "familyMember": "father",
            "medicalProblem": "Heart disease, died at age 65"
        },
        {
            "familyMember": "mother",
            "medicalProblem": "Diabetes, hypertension"
        },
        {
            "familyMember": "brother",
            "medicalProblem": "High cholesterol"
        }
    ],
    "pastSurgicalHistory": [
        {
            "surgeryType": "Appendectomy",
            "year": 1995
        },
        {
            "surgeryType": "Cholecystectomy",
            "year": 2018
        }
    ],
    "specificConditions": {
        "gerdHeartburn": {
            "hasGerd": True,
            "gerdDetails": "Occasional heartburn, worse with spicy foods"
        },
        "pancreatitis": {
            "hasPancreatitis": False
        }
    },
    "socialHistory": {
        "smokingSummary": "Former smoker, quit 10 years ago, 20 pack-year history",
        "alcoholSummary": "Social drinker, 2-3 drinks per week",
        "marijuanaSummary": "Never used",
        "drugSummary": "No history of recreational drug use",
        "employmentStatus": "Employed",
        "employmentDetails": "Software engineer, sedentary work",
        "financialSituation": "Stable, middle income",
        "educationBackground": "Bachelor's degree in Computer Science"
    }
}

async def test_medical_history_push():
    """Test pushing complete medical history data to Charm"""
    try:
        # Use the patient_id from previous tests
        patient_id = "1043817000084754508"
        
        logger.info(f"Testing medical history push for patient_id: {patient_id}")
        logger.info("Medical history data to push:")
        logger.info(json.dumps(test_medical_history_data, indent=2))
        
        # Call the medical history push function
        logger.info("\n=== Calling push_intake_section for medical_history ===")
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=test_medical_history_data
        )
        
        if success:
            logger.info("✅ Medical history push successful!")
            logger.info("This should have resulted in:")
            logger.info("1. 3 medications added to Medication API")
            logger.info("2. 2 allergies added to Allergy API")
            logger.info("3. Past medical history added with 6 conditions")
            logger.info("4. Social history added with smoking, alcohol, employment details")
            logger.info("5. 3 family history entries added")
            logger.info("6. 2 past surgeries added as procedures")
        else:
            logger.error("❌ Medical history push failed!")
            
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

# Test with partial data scenarios
async def test_medications_only():
    """Test with only medications data"""
    try:
        patient_id = "1043817000084754508"
        
        medications_only_data = {
            "currentMedications": [
                {
                    "medicationName": "Ibuprofen",
                    "strength": "400mg",
                    "directions": "Take as needed for pain, max 3 times daily"
                }
            ]
        }
        
        logger.info("\n=== Testing medications only ===")
        logger.info(f"Data: {json.dumps(medications_only_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=medications_only_data
        )
        
        if success:
            logger.info("✅ Medications-only push successful!")
        else:
            logger.error("❌ Medications-only push failed!")
            
    except Exception as e:
        logger.error(f"Error during medications-only test: {e}", exc_info=True)

async def test_allergies_only():
    """Test with only allergies data"""
    try:
        patient_id = "1043817000084754508"
        
        allergies_only_data = {
            "allergies": [
                {
                    "allergen": "Latex",
                    "reaction": "Contact dermatitis",
                    "severity": "Mild"
                },
                {
                    "allergen": "Peanuts",
                    "reaction": "Anaphylaxis",
                    "severity": "Severe"
                }
            ]
        }
        
        logger.info("\n=== Testing allergies only ===")
        logger.info(f"Data: {json.dumps(allergies_only_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=allergies_only_data
        )
        
        if success:
            logger.info("✅ Allergies-only push successful!")
        else:
            logger.error("❌ Allergies-only push failed!")
            
    except Exception as e:
        logger.error(f"Error during allergies-only test: {e}", exc_info=True)

async def test_social_history_only():
    """Test with only social history data"""
    try:
        patient_id = "1043817000084754508"
        
        social_only_data = {
            "socialHistory": {
                "smokingSummary": "Current smoker, 1 pack per day for 15 years",
                "alcoholSummary": "Heavy drinker, 6+ drinks daily",
                "employmentStatus": "Unemployed",
                "educationBackground": "High school diploma"
            }
        }
        
        logger.info("\n=== Testing social history only ===")
        logger.info(f"Data: {json.dumps(social_only_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="medical_history",
            patient_id=patient_id,
            section_data=social_only_data
        )
        
        if success:
            logger.info("✅ Social history-only push successful!")
        else:
            logger.error("❌ Social history-only push failed!")
            
    except Exception as e:
        logger.error(f"Error during social history-only test: {e}", exc_info=True)

if __name__ == "__main__":
    async def run_all_tests():
        await test_medical_history_push()
        await test_medications_only()
        await test_allergies_only()
        await test_social_history_only()
    
    asyncio.run(run_all_tests())