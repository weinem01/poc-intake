"""
Test script to push weight history data including vitals and bariatric surgery info
"""

import asyncio
import json
import logging
from app.services.ehr_service import ehr_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data from the provided JSON
test_weight_history_data = {
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
        "hasBariatricSurgeryHistory": True,
        "surgeryType": ["Gastric bypass"],
        "surgeryYear": 2008,
        "preSurgeryWeight": 300,
        "lowestWeightAfterSurgery": 180
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
}

async def test_weight_history_push():
    """Test pushing weight history data to Charm"""
    try:
        # Use the patient_id from the previous test
        patient_id = "1043817000084754508"
        
        logger.info(f"Testing weight history push for patient_id: {patient_id}")
        logger.info("Weight history data to push:")
        logger.info(json.dumps(test_weight_history_data, indent=2))
        
        # Call the weight history push function
        logger.info("\n=== Calling push_intake_section for weight_history ===")
        success = await ehr_service.push_intake_section(
            section_type="weight_history",
            patient_id=patient_id,
            section_data=test_weight_history_data
        )
        
        if success:
            logger.info("✅ Weight history push successful!")
            logger.info("This should have resulted in:")
            logger.info("1. Vitals API call with height 6'2\" and weight 210 lbs")
            logger.info("2. Patient API call with bariatric surgery info:")
            logger.info("   - custom_field_1: 'Gastric bypass'")
            logger.info("   - custom_field_2: '2008'")
        else:
            logger.error("❌ Weight history push failed!")
            
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

# Test with different scenarios
async def test_vitals_only():
    """Test with only vitals data (no bariatric surgery)"""
    try:
        patient_id = "1043817000084754508"
        
        vitals_only_data = {
            "currentVitals": {
                "height": {"feet": 5, "inches": 8},
                "weight": 150
            },
            "bariatricSurgeryHistory": {
                "hasBariatricSurgeryHistory": False
            }
        }
        
        logger.info("\n=== Testing vitals only (no bariatric surgery) ===")
        logger.info(f"Data: {json.dumps(vitals_only_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="weight_history",
            patient_id=patient_id,
            section_data=vitals_only_data
        )
        
        if success:
            logger.info("✅ Vitals-only push successful!")
        else:
            logger.error("❌ Vitals-only push failed!")
            
    except Exception as e:
        logger.error(f"Error during vitals-only test: {e}", exc_info=True)

async def test_bariatric_only():
    """Test with only bariatric surgery data (no vitals)"""
    try:
        patient_id = "1043817000084754508"
        
        bariatric_only_data = {
            "bariatricSurgeryHistory": {
                "hasBariatricSurgeryHistory": True,
                "surgeryType": ["Sleeve gastrectomy", "Revision"],
                "surgeryYear": 2015
            }
        }
        
        logger.info("\n=== Testing bariatric surgery only (no vitals) ===")
        logger.info(f"Data: {json.dumps(bariatric_only_data, indent=2)}")
        
        success = await ehr_service.push_intake_section(
            section_type="weight_history",
            patient_id=patient_id,
            section_data=bariatric_only_data
        )
        
        if success:
            logger.info("✅ Bariatric-only push successful!")
            logger.info("Should have set:")
            logger.info("   - custom_field_1: 'Sleeve gastrectomy, Revision'")
            logger.info("   - custom_field_2: '2015'")
        else:
            logger.error("❌ Bariatric-only push failed!")
            
    except Exception as e:
        logger.error(f"Error during bariatric-only test: {e}", exc_info=True)

if __name__ == "__main__":
    async def run_all_tests():
        await test_weight_history_push()
        await test_vitals_only()
        await test_bariatric_only()
    
    asyncio.run(run_all_tests())