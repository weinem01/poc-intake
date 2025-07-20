import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.services.ehr_service import _create_diagnosis_agent

async def test_agent():
    print("Testing diagnosis agent creation...")
    
    try:
        # Test agent creation
        agent = _create_diagnosis_agent()
        print("✓ Agent created successfully")
        
        # Test simple run
        test_input = "Patient: 30 year old male, BMI 28, high blood pressure"
        print(f"Testing with input: {test_input}")
        
        result = await agent.run(f"Analyze this patient data: {test_input}")
        print(f"✓ Agent run successful")
        print(f"Result type: {type(result)}")
        print(f"Result data type: {type(result.data)}")
        print(f"Recommended diagnoses: {len(result.data.recommended_diagnoses)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())