"""
Test for the push_diagnosis_to_charm function using real AI agent analysis
This test uses actual sample intake data and makes real API calls to test the full flow
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the parent directory to the path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verify OpenAI API key is available
openai_key = os.getenv('OPENAI_API_KEY')
if not openai_key:
    logger.error("❌ OPENAI_API_KEY not found in environment variables")
    logger.error("Please ensure the .env file contains a valid OPENAI_API_KEY")
    sys.exit(1)
else:
    logger.info(f"✅ OpenAI API key loaded (ends with: ...{openai_key[-4:]})")

# Import the EHR service
from app.services.ehr_service import ehr_service

# Sample intake data provided by the user
SAMPLE_INTAKE_DATA = {
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
        "record_id": "POC16872",
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
        "careTeamProviders": [
            {
                "specialty": "internal medicine",
                "practiceName": "ACP",
                "relationshipType": "Primary Care Physician",
                "isPrimaryCarePhysician": True
            }
        ],
        "communicationPreferences": {
            "preferredMethod": "email",
            "textNotifications": True,
            "emailNotifications": True,
            "voiceNotifications": True
        }
    },
    "intake_weight_history": {
        "isComplete": True,
        "dietHistory": {
            "pastDietsTried": ["keto", "calorie counting", "vegan"],
            "typicalDayEating": {
                "lunch": "salad, chicken vegetables",
                "dinner": "fast food",
                "beverages": "coffee, water",
                "breakfast": "coffee and fruit",
                "snacksDesserts": "chips, candy"
            },
            "strugglesWithDiet": "Always loses a few pounds then gives up and gains the weight back every time",
            "weightGainFactors": {
                "alcohol": "1-2 drinks per week",
                "genetics": True,
                "injuries": "broke my ankle and gained 20 lbs",
                "menopause": False,
                "pregnancy": False,
                "nightShiftWork": False,
                "childhoodTrauma": False,
                "quittingSmoking": False,
                "artificialSweetener": "a few times a week - usually in my coffee",
                "processedFoodAddictions": "jalapeno potato chips",
                "sugarContainingBeverages": "never",
                "weightGainingMedications": [],
                "chronicStressOrDepression": False
            }
        },
        "currentVitals": {
            "height": {"feet": 6, "inches": 2},
            "weight": 210
        },
        "weightHistory": {
            "ageAtMaxWeight": 25,
            "maxEverWeighed": 300,
            "maxWeightLostByDieting": 20
        },
        "exerciseInformation": "Lifts weights two days a week",
        "treatmentPreferences": {
            "treatmentApproach": "Whatever you think is best"
        },
        "bariatricSurgeryHistory": {
            "hasBariatricSurgeryHistory": False
        },
        "weightLossMedicationHistory": {
            "glp1Medications": {
                "semaglutide": {"hasTried": False},
                "tirzepatide": {
                    "hasTried": True,
                    "brandNames": ["Zepbound"],
                    "weightLost": 20,
                    "highestDose": "5mg",
                    "treatmentDuration": "6 months"
                },
                "hasTriedGlp1": True
            },
            "otherWeightLossMedications": []
        }
    },
    "intake_medical_history": {
        "PMHx": ["High blood pressure", "Pre-diabetes"],
        "isComplete": True,
        "familyHistory": [
            {
                "familyMember": "father",
                "medicalProblem": "High blood pressure"
            },
            {
                "familyMember": "mother",
                "medicalProblem": "High blood pressure"
            }
        ],
        "socialHistory": {
            "drugSummary": "no other drugs",
            "alcoholSummary": "1-2 times a week",
            "smokingSummary": "Used to smoke as a kid",
            "employmentStatus": "employed full time",
            "marijuanaSummary": "never",
            "employmentDetails": "weight loss surgeon",
            "financialSituation": "fine, no issues",
            "educationBackground": "Doctor (MD)"
        },
        "currentMedications": [
            {
                "strength": "10mg",
                "directions": "daily",
                "medicationName": "losartan"
            }
        ],
        "specificConditions": {
            "pancreatitis": {"hasPancreatitis": False},
            "gerdHeartburn": {"hasGerd": False}
        },
        "PMHxObesityComorbid": ["Sleep apnea"],
        "pastSurgicalHistory": [
            {
                "year": 2008,
                "surgeryType": "umbilical hernia repair"
            }
        ]
    },
    "intake_demographics_tracking": {
        "isComplete": True,
        "unasked_fields": [],
        "pushed_to_charm": False
    },
    "intake_weight_history_tracking": {
        "isComplete": True,
        "unasked_fields": [],
        "pushed_to_charm": False
    },
    "intake_medical_history_tracking": {
        "isComplete": True,
        "unasked_fields": [],
        "pushed_to_charm": False
    }
}

async def test_push_diagnosis_to_charm():
    """
    Test the push_diagnosis_to_charm function with real sample data
    This will actually run the AI agent and make API calls
    """
    try:
        logger.info("=== Testing push_diagnosis_to_charm Function ===")
        
        # Extract patient ID from the sample data
        patient_id = SAMPLE_INTAKE_DATA["intake_demographics"]["patient_id"]
        logger.info(f"Using patient ID: {patient_id}")
        
        # Log what we're about to analyze
        logger.info("=== Sample Data Analysis ===")
        
        # Extract key information for logging
        demographics = SAMPLE_INTAKE_DATA.get("intake_demographics", {})
        weight_history = SAMPLE_INTAKE_DATA.get("intake_weight_history", {})
        medical_history = SAMPLE_INTAKE_DATA.get("intake_medical_history", {})
        
        logger.info(f"Patient: {demographics.get('firstName')} {demographics.get('lastName')}")
        logger.info(f"Gender: {demographics.get('gender')}")
        logger.info(f"DOB: {demographics.get('dateOfBirth')}")
        
        # Current vitals
        current_vitals = weight_history.get("currentVitals", {})
        height = current_vitals.get("height", {})
        weight = current_vitals.get("weight")
        if height and weight:
            feet = height.get("feet", 0)
            inches = height.get("inches", 0)
            total_inches = (feet * 12) + inches
            if total_inches > 0:
                bmi = (weight / (total_inches ** 2)) * 703
                logger.info(f"Height: {feet}'{inches}\" ({total_inches} inches)")
                logger.info(f"Weight: {weight} lbs")
                logger.info(f"Calculated BMI: {bmi:.1f}")
        
        # Medical history
        pmhx = medical_history.get("PMHx", [])
        pmhx_obesity = medical_history.get("PMHxObesityComorbid", [])
        all_conditions = pmhx + pmhx_obesity
        if all_conditions:
            logger.info(f"Past Medical History: {', '.join(all_conditions)}")
        
        medications = medical_history.get("currentMedications", [])
        if medications:
            med_list = [f"{med.get('medicationName', 'Unknown')} {med.get('strength', '')}" for med in medications]
            logger.info(f"Current Medications: {', '.join(med_list)}")
        
        logger.info("=== Running AI Diagnosis Agent ===")
        
        # Call the actual function - this will run the AI agent and make API calls
        success = await ehr_service.push_diagnosis_to_charm(patient_id, SAMPLE_INTAKE_DATA)
        
        # Log the result
        if success:
            logger.info("✅ push_diagnosis_to_charm completed successfully!")
            logger.info("   - AI agent analyzed the intake data")
            logger.info("   - Diagnoses were recommended based on patient data") 
            logger.info("   - Diagnoses were successfully pushed to Charm API")
        else:
            logger.error("❌ push_diagnosis_to_charm failed")
            logger.error("   This could be due to:")
            logger.error("   - AI agent analysis failure")
            logger.error("   - API connectivity issues")
            logger.error("   - Authentication problems")
            logger.error("   - Data formatting issues")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Exception during diagnosis push test: {e}", exc_info=True)
        return False

async def verify_patient_exists():
    """
    Verify that the patient exists in the system before running diagnosis test
    """
    try:
        logger.info("=== Verifying Patient Exists ===")
        
        record_id = SAMPLE_INTAKE_DATA["intake_demographics"]["record_id"]
        logger.info(f"Looking up patient with record ID: {record_id}")
        
        patient_data = await ehr_service.validate_patient_by_mrn(record_id)
        
        if patient_data:
            logger.info("✅ Patient found in system")
            logger.info(f"   Patient ID: {patient_data.get('patient_id', 'Unknown')}")
            logger.info(f"   Name: {patient_data.get('first_name', '')} {patient_data.get('last_name', '')}")
            return True
        else:
            logger.error("❌ Patient not found in system")
            logger.error(f"   Record ID {record_id} does not exist")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error validating patient: {e}", exc_info=True)
        return False

async def run_diagnosis_test():
    """
    Run the complete diagnosis test workflow
    """
    logger.info("Starting diagnosis push test with real AI agent...")
    
    # Step 1: Verify the patient exists
    patient_exists = await verify_patient_exists()
    if not patient_exists:
        logger.error("❌ Cannot proceed - patient does not exist in system")
        return
    
    # Step 2: Run the diagnosis analysis and push test
    test_success = await test_push_diagnosis_to_charm()
    
    # Final summary
    if test_success:
        logger.info("🎉 All tests passed! Diagnosis push workflow is working correctly")
        logger.info("   The AI agent successfully:")
        logger.info("   - Analyzed the patient intake data")
        logger.info("   - Generated appropriate diagnosis recommendations")
        logger.info("   - Pushed the diagnoses to the Charm EHR system")
    else:
        logger.error("❌ Test failed - check logs above for details")

if __name__ == "__main__":
    # Run the test
    asyncio.run(run_diagnosis_test())