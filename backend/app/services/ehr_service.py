"""
EHR API service for patient validation and data operations
Uses the Charm Tracker API with token management
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from app.core.token_manager import get_charm_api_headers
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DiagnosisRecommendation(BaseModel):
    """Model for recommended diagnoses based on patient intake data"""
    name: str = Field(description="The full name of the diagnosis")
    code: str = Field(description="The ICD-10 code for the diagnosis")
    code_type: str = Field(default="ICD10", description="The type of code, typically ICD10")
    status: str = Field(default="Active", description="Status of the diagnosis")
    comments: Optional[str] = Field(default=None, description="Additional comments about the diagnosis")
    reasoning: str = Field(description="Explanation for why this diagnosis was recommended")


class DiagnosisAnalysis(BaseModel):
    """Model for complete diagnosis analysis results"""
    bmi: Optional[float] = Field(description="Calculated BMI from height and weight")
    bmi_category: Optional[str] = Field(description="BMI category (Normal, Overweight, Obese, etc.)")
    recommended_diagnoses: List[DiagnosisRecommendation] = Field(description="List of recommended diagnoses")
    analysis_notes: str = Field(description="Overall analysis notes")


def _load_diagnosis_list() -> str:
    """Load the diagnosis list from the markdown file"""
    try:
        import os
        diagnosis_file_path = os.path.join(os.path.dirname(__file__), "../../../.vscode/Diagnosis List for AI Scribe.md")
        with open(diagnosis_file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading diagnosis list: {e}")
        return "Error loading diagnosis list - using default set"


def _create_diagnosis_agent() -> Agent:
    """Create the diagnosis agent with dynamic diagnosis list"""
    diagnosis_list = _load_diagnosis_list()
    
    # For now, let's just return a string model name to avoid the isinstance error
    # TODO: Fix package version compatibility issue
    
    system_prompt = f"""You are a medical diagnosis assistant that analyzes patient intake data to recommend appropriate ICD-10 diagnoses.

Available diagnoses from the clinic's approved list:
{diagnosis_list}

BMI Calculation: BMI = weight(lbs) / (height(inches)^2) * 703

Instructions:
1. Calculate BMI from height and weight if available
2. Determine appropriate BMI-related diagnoses based on the calculated BMI
3. Review medical history for conditions that match available diagnoses from the list above
4. Consider weight-related comorbidities mentioned in the intake
5. Include bariatric surgery history if mentioned
6. Only recommend diagnoses that are explicitly listed in the available diagnoses above
7. Use the exact diagnosis names and ICD-10 codes from the list
8. Provide clear reasoning for each recommendation based on the intake data"""

    return Agent(
        'gpt-4o-mini',
        result_type=DiagnosisAnalysis,
        system_prompt=system_prompt,
    )


class EHRService:
    """Service for interacting with Charm Tracker EHR API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.charm_api_base_url
        self.facility_id = self.settings.charm_facility_id
    
    async def validate_patient_by_mrn(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate patient exists using the /patients endpoint
        Returns patient data if found, None if not found
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/patients",
                    params={
                        "record_id": record_id,
                        "facility_id": "ALL"
                    },
                    headers=headers,
                    timeout=30.0
                )
                print(response)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "0" and data.get("patients") and len(data["patients"]) > 0:
                        logger.info(f"Patient found for MRN {record_id}")
                        return data["patients"][0]  # Return first matching patient
                    else:
                        logger.warning(f"No patient found for MRN {record_id}")
                        return None
                elif response.status_code == 404:
                    logger.warning(f"Patient not found for MRN {record_id}")
                    return None
                elif response.status_code == 400:
                    logger.warning(f"Invalid MRN format or patient not found: {record_id}")
                    return None
                else:
                    logger.error(f"API error validating patient {record_id}: {response.status_code} - {response.text}")
                    response.raise_for_status()
                    
        except Exception as e:
            logger.error(f"Error validating patient {record_id}: {e}")
            raise
    
    async def get_payers_list(self) -> List[Dict[str, Any]]:
        """
        Get list of payers from the EHR API
        Used for insurance validation and lookup
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payers",
                    params={"facility_id": "ALL"},
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Retrieved {len(data)} payers from EHR")
                return data
                
        except Exception as e:
            logger.error(f"Error retrieving payers list: {e}")
            raise
    
    async def search_providers(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for providers in the EHR directory
        Used for care team provider lookup
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/settings/directory/providers",
                    params={"search": search_term},
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Found {len(data)} providers for search term: {search_term}")
                return data
                
        except Exception as e:
            logger.error(f"Error searching providers for '{search_term}': {e}")
            raise
    
    async def add_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new provider to the EHR directory
        Used when a provider is not found in the existing directory
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/settings/directory/providers",
                    json=provider_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Added new provider: {provider_data.get('name', 'Unknown')}")
                return data
                
        except Exception as e:
            logger.error(f"Error adding provider: {e}")
            raise
    
    async def update_patient_demographics(self, patient_id: str, demographics_data: Dict[str, Any]) -> bool:
        """
        Update patient demographics in the EHR
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/patients/{patient_id}",
                    json=demographics_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                logger.info(f"Updated demographics for patient {patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating patient demographics for {patient_id}: {e}")
            raise
    
    async def update_patient_insurance(self, patient_id: str, insurance_data: Dict[str, Any]) -> bool:
        """
        Update patient insurance information in the EHR
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/patients/{patient_id}/insurance",
                    json=insurance_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                logger.info(f"Updated insurance for patient {patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating patient insurance for {patient_id}: {e}")
            raise
    
    async def add_patient_vitals(self, patient_id: str, vitals_data: Dict[str, Any]) -> bool:
        """
        Add patient vitals (height, weight) to the EHR
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/patients/{patient_id}/vitals",
                    json=vitals_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                logger.info(f"Added vitals for patient {patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding patient vitals for {patient_id}: {e}")
            raise
    
    async def add_patient_medications(self, patient_id: str, medications_data: List[Dict[str, Any]]) -> bool:
        """
        Add patient medications to the EHR
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                for medication in medications_data:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/medications",
                        json=medication,
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                
                logger.info(f"Added {len(medications_data)} medications for patient {patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding patient medications for {patient_id}: {e}")
            raise
    
    async def add_patient_allergies(self, patient_id: str, allergies_data: List[Dict[str, Any]]) -> bool:
        """
        Add patient allergies to the EHR
        """
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                for allergy in allergies_data:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/allergies",
                        json=allergy,
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                
                logger.info(f"Added {len(allergies_data)} allergies for patient {patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding patient allergies for {patient_id}: {e}")
            raise
    
    async def push_intake_section(self, section_type: str, patient_id: str, section_data: Dict[str, Any]) -> bool:
        """
        Push completed intake section data to appropriate Charm APIs
        
        Args:
            section_type: Type of section ("demographics", "medical_history", "weight_history", "insurance")
            patient_id: Charm patient ID
            section_data: The intake data for the section
            
        Returns:
            bool: True if push was successful, False otherwise
        """
        try:
            if section_type == "demographics":
                return await self._push_demographics_to_charm(patient_id, section_data)
            elif section_type == "medical_history":
                return await self._push_medical_history_to_charm(patient_id, section_data)
            elif section_type == "weight_history":
                return await self._push_weight_history_to_charm(patient_id, section_data)
            elif section_type == "insurance":
                # TODO: Implement insurance push
                logger.warning(f"Insurance push not yet implemented")
                return False
            else:
                logger.error(f"Unknown section type: {section_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error pushing {section_type} section: {e}")
            return False
    
    async def _push_demographics_to_charm(self, patient_id: str, demographics_data: Dict[str, Any]) -> bool:
        """
        Push demographics data to Charm Patient API
        Maps intake_demographics fields to Charm API fields
        """
        try:
            # Get headers for API calls
            headers = await get_charm_api_headers()
            
            # Map intake_demographics to Charm API format
            charm_data = {
                # Required fields
                "first_name": demographics_data.get("firstName", ""),
                "last_name": demographics_data.get("lastName", ""),
                "gender": demographics_data.get("gender", "").lower(),
                "dob": demographics_data.get("dateOfBirth", ""),
                "record_id": demographics_data.get("record_id", ""),
                "facilities": [{"facility_id": "ALL"}],
                
                # Optional fields
                "update_specific_details": True  # Only update fields we send
            }
            
            # Add middle name if present
            if demographics_data.get("middleName"):
                charm_data["middle_name"] = demographics_data["middleName"]
            
            # Add email if present
            if demographics_data.get("email"):
                charm_data["email"] = demographics_data["email"]
            
            # Map phone numbers
            phone_info = demographics_data.get("phone", {})
            if phone_info.get("mobile"):
                charm_data["mobile"] = phone_info["mobile"]
            if phone_info.get("home"):
                charm_data["home_phone"] = phone_info["home"]
            if phone_info.get("work"):
                charm_data["work_phone"] = phone_info["work"]
            if phone_info.get("workExtension"):
                charm_data["work_phone_extn"] = phone_info["workExtension"]
            
            # Map preferred phone
            preferred = phone_info.get("preferred")
            if preferred:
                preferred_map = {
                    "mobile": "Mobile Phone",
                    "home": "Home Phone",
                    "work": "Work Phone"
                }
                charm_data["primary_phone"] = preferred_map.get(preferred, "Mobile Phone")
            
            # Map address
            address = demographics_data.get("address", {})
            if address:
                charm_data["address"] = {
                    "address_line1": address.get("addressLine1", ""),
                    "address_line2": address.get("addressLine2", ""),
                    "city": address.get("city", ""),
                    "state": address.get("state", ""),
                    "country": address.get("country", "us"),
                    "zip_code": address.get("zipCode", "")
                }
            
            # Map emergency contact
            emergency = demographics_data.get("emergencyContact", {})
            if emergency.get("name"):
                charm_data["emergency_contact_name"] = emergency["name"]
            if emergency.get("phone"):
                charm_data["emergency_contact_number"] = emergency["phone"]
            
            # Map communication preferences
            comm_prefs = demographics_data.get("communicationPreferences", {})
            if "emailNotifications" in comm_prefs:
                charm_data["email_notification"] = comm_prefs["emailNotifications"]
            if "textNotifications" in comm_prefs:
                charm_data["text_notification"] = comm_prefs["textNotifications"]
            if "voiceNotifications" in comm_prefs:
                charm_data["voice_notification"] = comm_prefs["voiceNotifications"]
            
            # Map preferred communication method
            pref_method = comm_prefs.get("preferredMethod")
            if pref_method:
                method_map = {
                    "email": "Email",
                    "phone": "Phone",
                    "text": "Phone",  # Text maps to Phone in Charm
                    "portal": "CHARM PHR"
                }
                charm_data["preferred_communication"] = method_map.get(pref_method, "Email")
            
            # Map marital status
            if demographics_data.get("maritalStatus"):
                charm_data["marital_status"] = demographics_data["maritalStatus"]
            
            # Map employment status
            if demographics_data.get("employmentStatus"):
                charm_data["employment_status"] = demographics_data["employmentStatus"]
            
            # Make the API call to update patient
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/patients/{patient_id}",
                    json=charm_data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully pushed demographics for patient {patient_id}")
                    return True
                else:
                    logger.error(f"Failed to push demographics: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pushing demographics for patient {patient_id}: {e}")
            return False
    
    async def _push_weight_history_to_charm(self, patient_id: str, weight_history_data: Dict[str, Any]) -> bool:
        """
        Push weight history data to appropriate Charm APIs
        This includes vitals (height/weight) and bariatric surgery info in patient custom fields
        """
        try:
            headers = await get_charm_api_headers()
            success_count = 0
            total_operations = 0
            
            # 1. Push current vitals to Vitals API
            current_vitals = weight_history_data.get("currentVitals", {})
            if current_vitals:
                total_operations += 1
                vitals_success = await self._push_vitals_to_charm(patient_id, current_vitals, headers)
                if vitals_success:
                    success_count += 1
                    logger.info(f"Successfully pushed vitals for patient {patient_id}")
                else:
                    logger.error(f"Failed to push vitals for patient {patient_id}")
            
            # 2. Push bariatric surgery info to Patient custom fields
            bariatric_history = weight_history_data.get("bariatricSurgeryHistory", {})
            if bariatric_history.get("hasBariatricSurgeryHistory"):
                total_operations += 1
                surgery_success = await self._push_bariatric_surgery_to_patient(patient_id, bariatric_history, headers)
                if surgery_success:
                    success_count += 1
                    logger.info(f"Successfully pushed bariatric surgery info for patient {patient_id}")
                else:
                    logger.error(f"Failed to push bariatric surgery info for patient {patient_id}")
            
            # Return success if all operations succeeded
            return success_count == total_operations and total_operations > 0
            
        except Exception as e:
            logger.error(f"Error pushing weight history for patient {patient_id}: {e}")
            return False
    
    async def _push_vitals_to_charm(self, patient_id: str, vitals_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Push height and weight to Vitals API using correct format"""
        try:
            from datetime import datetime
            
            # Get current date for entry_date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Map height and weight to Charm vitals format
            height_data = vitals_data.get("height", {})
            weight = vitals_data.get("weight")
            
            vitals_array = []
            
            # Add weight vital if present
            if weight:
                vitals_array.extend([
                    {
                        "vital_name": "Weight",
                        "vital_value": str(weight),
                        "vital_unit": "lbs"
                    },
                    {
                        "vital_name": "Weight", 
                        "vital_value": "",
                        "vital_unit": "ozs"
                    }
                ])
            
            # Add height vitals if present
            if height_data:
                feet = height_data.get("feet", 0)
                inches = height_data.get("inches", 0)
                
                vitals_array.extend([
                    {
                        "vital_name": "Height",
                        "vital_value": str(feet),
                        "vital_unit": "ft"
                    },
                    {
                        "vital_name": "Height",
                        "vital_value": str(inches),
                        "vital_unit": "ins"
                    }
                ])
            
            # Only make API call if we have vitals to send
            if vitals_array:
                # Create single vitals entry object
                vitals_entry = {
                    "entry_date": current_date,
                    "vitals": vitals_array
                }
                
                # Wrap in array as required by API
                vitals_payload = [vitals_entry]
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/vitals",
                        json=vitals_payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Pushed vitals: Weight {weight} lbs, Height {feet}'{inches}\"")
                        return True
                    else:
                        logger.error(f"Vitals API error: {response.status_code} - {response.text}")
                        return False
            
            return True  # No vitals to push is considered success
            
        except Exception as e:
            logger.error(f"Error pushing vitals: {e}")
            return False
    
    async def _get_patient_details(self, patient_id: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get current patient details from Charm API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/patients/{patient_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "0" and data.get("patient"):
                        return data["patient"]
                    else:
                        logger.error(f"Failed to get patient details: {data}")
                        return None
                else:
                    logger.error(f"Failed to get patient details: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting patient details: {e}")
            return None
    
    async def _push_bariatric_surgery_to_patient(self, patient_id: str, bariatric_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Push bariatric surgery info to Patient custom fields"""
        try:
            surgery_types = bariatric_data.get("surgeryType", [])
            surgery_year = bariatric_data.get("surgeryYear")
            
            # Only proceed if we have surgery data to update
            if not surgery_types and not surgery_year:
                return True  # No surgery data to push is considered success
            
            # Get current patient details to include required fields
            patient_details = await self._get_patient_details(patient_id, headers)
            if not patient_details:
                logger.error(f"Could not get patient details for {patient_id}, cannot update bariatric surgery info")
                return False
            
            # Prepare patient update payload with required fields
            patient_update = {
                # Required fields from current patient data
                "first_name": patient_details.get("first_name", ""),
                "last_name": patient_details.get("last_name", ""),
                "gender": patient_details.get("gender", ""),
                "dob": patient_details.get("dob", ""),
                "facilities": patient_details.get("facilities", [{"facility_id": "ALL"}]),
                "record_id": patient_details.get("record_id", ""),
                "update_specific_details": True
            }
            
            # Add bariatric surgery custom fields
            if surgery_types:
                # Join multiple surgery types with comma if multiple
                surgery_name = ", ".join(surgery_types) if isinstance(surgery_types, list) else str(surgery_types)
                patient_update["custom_field_1"] = surgery_name
                
            if surgery_year:
                patient_update["custom_field_2"] = str(surgery_year)
            
            # Make API call to update patient
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/patients/{patient_id}",
                    json=patient_update,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    surgery_name = ", ".join(surgery_types) if surgery_types else "N/A"
                    logger.info(f"Added bariatric surgery info: {surgery_name} in {surgery_year if surgery_year else 'unknown year'}")
                    return True
                else:
                    logger.error(f"Patient update API error: {response.status_code} - {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Error pushing bariatric surgery info: {e}")
            return False
    
    async def _push_medical_history_to_charm(self, patient_id: str, medical_history_data: Dict[str, Any]) -> bool:
        """
        Push medical history data to appropriate Charm APIs
        This includes medications, allergies, past medical history, social history, family history, and past surgeries
        """
        try:
            headers = await get_charm_api_headers()
            success_count = 0
            total_operations = 0
            
            # 1. Push current medications to Medication API
            current_medications = medical_history_data.get("currentMedications", [])
            if current_medications:
                total_operations += 1
                meds_success = await self._push_medications_to_charm(patient_id, current_medications, headers)
                if meds_success:
                    success_count += 1
                    logger.info(f"Successfully pushed {len(current_medications)} medications for patient {patient_id}")
                else:
                    logger.error(f"Failed to push medications for patient {patient_id}")
            
            # 2. Push allergies to Allergy API
            allergies = medical_history_data.get("allergies", [])
            if allergies:
                total_operations += 1
                allergies_success = await self._push_allergies_to_charm(patient_id, allergies, headers)
                if allergies_success:
                    success_count += 1
                    logger.info(f"Successfully pushed {len(allergies)} allergies for patient {patient_id}")
                else:
                    logger.error(f"Failed to push allergies for patient {patient_id}")
            
            # 3. Push past medical history to Medical History API
            pmhx = medical_history_data.get("PMHx", [])
            pmhx_obesity = medical_history_data.get("PMHxObesityComorbid", [])
            if pmhx or pmhx_obesity:
                total_operations += 1
                # Combine regular PMHx and obesity-related conditions
                all_conditions = (pmhx or []) + (pmhx_obesity or [])
                pmhx_success = await self._push_past_medical_history_to_charm(patient_id, all_conditions, headers)
                if pmhx_success:
                    success_count += 1
                    logger.info(f"Successfully pushed past medical history for patient {patient_id}")
                else:
                    logger.error(f"Failed to push past medical history for patient {patient_id}")
            
            # 4. Push social history to Medical History API
            social_history = medical_history_data.get("socialHistory")
            if social_history:
                total_operations += 1
                social_success = await self._push_social_history_to_charm(patient_id, social_history, headers)
                if social_success:
                    success_count += 1
                    logger.info(f"Successfully pushed social history for patient {patient_id}")
                else:
                    logger.error(f"Failed to push social history for patient {patient_id}")
            
            # 5. Push family history to Medical History API
            family_history = medical_history_data.get("familyHistory", [])
            if family_history:
                total_operations += 1
                family_success = await self._push_family_history_to_charm(patient_id, family_history, headers)
                if family_success:
                    success_count += 1
                    logger.info(f"Successfully pushed {len(family_history)} family history entries for patient {patient_id}")
                else:
                    logger.error(f"Failed to push family history for patient {patient_id}")
            
            # 6. Push past surgeries to Medical History API
            past_surgeries = medical_history_data.get("pastSurgicalHistory", [])
            if past_surgeries:
                total_operations += 1
                surgery_success = await self._push_past_surgeries_to_charm(patient_id, past_surgeries, headers)
                if surgery_success:
                    success_count += 1
                    logger.info(f"Successfully pushed {len(past_surgeries)} past surgeries for patient {patient_id}")
                else:
                    logger.error(f"Failed to push past surgeries for patient {patient_id}")
            
            # Return success if all operations succeeded
            return success_count == total_operations and total_operations > 0
            
        except Exception as e:
            logger.error(f"Error pushing medical history for patient {patient_id}: {e}")
            return False
    
    async def _push_medications_to_charm(self, patient_id: str, medications: List[Dict[str, Any]], headers: Dict[str, str]) -> bool:
        """Push medications to Charm Medication API"""
        try:
            medication_entries = []
            
            for med in medications:
                med_name = med.get("medicationName", "")
                strength = med.get("strength", "")
                directions = med.get("directions", "")
                
                if not med_name:
                    continue
                
                # Create medication entry according to API spec
                med_entry = {
                    "drug_name": med_name,
                    "strength_description": strength or "",
                    "directions": directions or "Take as directed",
                    "is_active": True,
                    "is_custom_drug": True,  # Since we're adding custom medications from intake
                    "dispense": 30.0,  # Default 30-day supply
                    "refills": "0",  # Default no refills
                    "substitute_generic": True,
                    "manufacturing_type": "Manufactured"
                }
                medication_entries.append(med_entry)
            
            # Send all medications in a single request (API expects array)
            if medication_entries:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/medications",
                        json=medication_entries,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Added {len(medication_entries)} medications")
                        return True
                    else:
                        logger.error(f"Failed to add medications: {response.status_code} - {response.text}")
                        return False
            
            return True  # No medications to push is considered success
            
        except Exception as e:
            logger.error(f"Error pushing medications: {e}")
            return False
    
    async def get_patient_allergies(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get existing allergies for a patient"""
        try:
            headers = await get_charm_api_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/patients/{patient_id}/allergies",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "0" and "allergies" in data:
                        return data["allergies"]
                    else:
                        logger.error(f"Unexpected response format: {data}")
                        return []
                else:
                    logger.error(f"Failed to get allergies: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting patient allergies: {e}")
            return []

    async def _push_allergies_to_charm(self, patient_id: str, allergies: List[Dict[str, Any]], headers: Dict[str, str]) -> bool:
        """Push allergies to Charm Allergy API - one at a time"""
        try:
            # Handle "no known allergies" case
            if not allergies or (len(allergies) == 1 and allergies[0].get("allergen", "").lower() in ["none", "nka", "no known allergies"]):
                logger.info(f"Patient has no known allergies, checking if we can mark as such")
                
                # First check if patient already has allergies
                existing_allergies = await self.get_patient_allergies(patient_id)
                if existing_allergies:
                    logger.warning(f"Cannot mark 'no known allergies' - patient already has {len(existing_allergies)} allergies recorded")
                    return False
                
                # Payload for no known allergies
                no_known_payload = {
                    "type": "Medication",
                    "status": "No Known"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/no_known_allergy",
                        json=no_known_payload,  # Send the required payload
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Successfully marked patient as having no known allergies")
                        return True
                    else:
                        logger.error(f"Failed to mark no known allergies: {response.status_code} - {response.text}")
                        return False
            
            # Process each allergy individually
            success_count = 0
            
            async with httpx.AsyncClient() as client:
                for allergy in allergies:
                    allergen = allergy.get("allergen", "")
                    reaction = allergy.get("reaction", "")
                    severity = allergy.get("severity", "")
                    
                    if not allergen:
                        continue
                    
                    # Skip "none" entries
                    if allergen.lower() in ["none", "nka", "no known allergies"]:
                        continue
                    
                    # Determine allergy type based on common patterns
                    allergen_lower = allergen.lower()
                    
                    # Check for specific types in order of specificity
                    if any(food in allergen_lower for food in ["peanut", "shellfish", "milk", "egg", "wheat", "soy", "fish", "tree nut", "gluten", "dairy"]):
                        allergy_type = "Food"
                    elif any(latex in allergen_lower for latex in ["latex", "rubber", "glove"]):
                        allergy_type = "Latex"
                    elif any(animal in allergen_lower for animal in ["cat", "dog", "pet", "dander", "fur", "animal"]):
                        allergy_type = "Animal"
                    elif any(plant in allergen_lower for plant in ["grass", "pollen", "tree", "weed", "ragweed", "flower"]):
                        allergy_type = "Plant"
                    elif any(env in allergen_lower for env in ["dust", "mold", "smoke", "perfume", "chemical"]):
                        allergy_type = "Environmental"
                    elif any(drug in allergen_lower for drug in ["penicillin", "aspirin", "ibuprofen", "sulfa", "antibiotic", "nsaid", "codeine", "morphine", "amoxicillin"]):
                        allergy_type = "Medication"  # Changed from "Drug" to "Medication"
                    else:
                        # Default to Medication for unrecognized allergens (most common)
                        allergy_type = "Medication"
                    
                    # Map severity - handle empty or None severity
                    if severity:
                        # Ensure proper capitalization
                        severity_map = {
                            "mild": "Mild",
                            "moderate": "Moderate", 
                            "severe": "Severe"
                        }
                        charm_severity = severity_map.get(severity.lower(), "Mild")
                    else:
                        charm_severity = "Moderate"  # Default severity
                    
                    # Create single allergy entry (NOT an array)
                    allergy_entry = {
                        "allergen": allergen.strip(),
                        "type": allergy_type,  # API expects 'type' not 'allergy_type'
                        "severity": charm_severity,
                        "reactions": (reaction or "").strip(),
                        "status": "Active"  # Changed from is_active: True to status: "Active"
                    }
                    
                    # Log what we're sending for debugging
                    logger.info(f"Sending allergy: {allergy_entry}")
                    
                    # Send single allergy (not wrapped in array)
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/allergies",
                        json=allergy_entry,  # Single object, not array
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.info(f"Successfully added allergy: {allergen}")
                    else:
                        logger.error(f"Failed to add allergy {allergen}: {response.status_code} - {response.text}")
                        logger.error(f"Request payload was: {allergy_entry}")
            
            # Return success if all allergies were added successfully
            total_allergies = len([a for a in allergies if a.get("allergen") and a.get("allergen").lower() not in ["none", "nka", "no known allergies"]])
            return success_count == total_allergies
            
        except Exception as e:
            logger.error(f"Error pushing allergies: {e}")
            return False
    
    async def _push_past_medical_history_to_charm(self, patient_id: str, conditions: List[str], headers: Dict[str, str]) -> bool:
        """Push past medical history to Charm Medical History API"""
        try:
            if not conditions:
                return True
            
            # Format conditions into a readable text
            pmhx_content = "Past Medical History:\\n" + "\\n".join([f"• {condition}" for condition in conditions])
            
            pmhx_payload = {
                "content": pmhx_content,
                "is_html": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/patients/{patient_id}/medicalhistory/pastmedicalhistory",
                    json=pmhx_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Added past medical history with {len(conditions)} conditions")
                    return True
                else:
                    logger.error(f"Failed to add past medical history: {response.status_code} - {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Error pushing past medical history: {e}")
            return False
    
    async def _push_social_history_to_charm(self, patient_id: str, social_history: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Push social history to Charm Medical History API"""
        try:
            # Format social history into readable text
            social_content_parts = []
            
            smoking = social_history.get("smokingSummary", "")
            if smoking:
                social_content_parts.append(f"Smoking: {smoking}")
            
            alcohol = social_history.get("alcoholSummary", "")
            if alcohol:
                social_content_parts.append(f"Alcohol: {alcohol}")
            
            marijuana = social_history.get("marijuanaSummary", "")
            if marijuana:
                social_content_parts.append(f"Marijuana: {marijuana}")
            
            drugs = social_history.get("drugSummary", "")
            if drugs:
                social_content_parts.append(f"Recreational Drugs: {drugs}")
            
            employment = social_history.get("employmentStatus", "")
            employment_details = social_history.get("employmentDetails", "")
            if employment or employment_details:
                emp_text = f"Employment: {employment}"
                if employment_details:
                    emp_text += f" - {employment_details}"
                social_content_parts.append(emp_text)
            
            financial = social_history.get("financialSituation", "")
            if financial:
                social_content_parts.append(f"Financial Situation: {financial}")
            
            education = social_history.get("educationBackground", "")
            if education:
                social_content_parts.append(f"Education: {education}")
            
            if not social_content_parts:
                return True  # No social history to push
            
            social_content = "Social History:\\n" + "\\n".join(social_content_parts)
            
            social_payload = {
                "content": social_content,
                "is_html": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/patients/{patient_id}/medicalhistory/socialhistory",
                    json=social_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info("Added social history")
                    return True
                else:
                    logger.error(f"Failed to add social history: {response.status_code} - {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Error pushing social history: {e}")
            return False
    
    async def _push_family_history_to_charm(self, patient_id: str, family_history: List[Dict[str, Any]], headers: Dict[str, str]) -> bool:
        """Push family history to Charm Medical History API"""
        try:
            success_count = 0
            
            for family_member in family_history:
                family_member_name = family_member.get("familyMember", "")
                medical_problem = family_member.get("medicalProblem", "")
                
                if not family_member_name or not medical_problem:
                    continue
                
                # Map family member relationships to Charm API format
                relationship_map = {
                    "father": "Natural Father",
                    "mother": "Natural Mother", 
                    "brother": "Natural Brother",
                    "sister": "Natural Sister",
                    "son": "Natural Son",
                    "daughter": "Natural Daughter",
                    "grandfather": "Paternal grandfather",
                    "grandmother": "Paternal grandmother"
                }
                
                relationship = relationship_map.get(family_member_name.lower(), "Natural Father")  # Default
                
                family_payload = {
                    "relationship": relationship,
                    "is_deceased": False,  # Default to alive
                    "comments": medical_problem
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/medicalhistory/familyhistory",
                        json=family_payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.info(f"Added family history: {family_member_name} - {medical_problem}")
                    else:
                        logger.error(f"Failed to add family history for {family_member_name}: {response.status_code} - {response.text}")
            
            return success_count == len(family_history)
            
        except Exception as e:
            logger.error(f"Error pushing family history: {e}")
            return False
    
    async def _push_past_surgeries_to_charm(self, patient_id: str, past_surgeries: List[Dict[str, Any]], headers: Dict[str, str]) -> bool:
        """Push past surgeries to Charm Medical History API procedure endpoint"""
        try:
            success_count = 0
            
            for surgery in past_surgeries:
                surgery_type = surgery.get("surgeryType", "")
                year = surgery.get("year")
                
                if not surgery_type:
                    continue
                
                # Format date from year
                surgery_date = f"{year}-01-01" if year else None
                
                surgery_payload = {
                    "procedure_type": "Surgeries",
                    "procedure": surgery_type,
                    "from_date": surgery_date,
                    "procedure_notes": ""
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/patients/{patient_id}/medicalhistory/procedure",
                        json=surgery_payload,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.info(f"Added past surgery: {surgery_type} ({year})")
                    else:
                        logger.error(f"Failed to add surgery {surgery_type}: {response.status_code} - {response.text}")
            
            return success_count == len(past_surgeries)
            
        except Exception as e:
            logger.error(f"Error pushing past surgeries: {e}")
            return False
    
    async def push_diagnosis_to_charm(self, patient_id: str, intake_data: Dict[str, Any]) -> bool:
        """
        Analyze intake data using Pydantic AI agent and push appropriate diagnoses to Charm
        
        Args:
            patient_id: Charm patient ID
            intake_data: Complete intake data including demographics, medical history, weight history
            
        Returns:
            bool: True if analysis and push was successful, False otherwise
        """
        try:
            logger.info(f"Creating diagnosis agent...")
            # Create the diagnosis agent with current diagnosis list
            diagnosis_agent = _create_diagnosis_agent()
            logger.info(f"Diagnosis agent created successfully")
            
            # Prepare intake data for analysis
            logger.info(f"Preparing intake data for analysis...")
            analysis_input = self._prepare_intake_for_diagnosis_analysis(intake_data)
            logger.info(f"Intake data prepared successfully")
            
            # Use Pydantic AI agent to analyze intake data and recommend diagnoses
            logger.info(f"Analyzing intake data for diagnosis recommendations for patient {patient_id}")
            result = await diagnosis_agent.run(
                f"Analyze this patient intake data and recommend appropriate diagnoses: {analysis_input}"
            )
            logger.info(f"Agent run completed successfully")
            
            diagnosis_analysis = result.output
            logger.info(f"Diagnosis analysis completed. BMI: {diagnosis_analysis.bmi}, Recommended diagnoses: {len(diagnosis_analysis.recommended_diagnoses)}")
            
            # Push recommended diagnoses to Charm API
            if diagnosis_analysis.recommended_diagnoses:
                success = await self._push_diagnoses_to_charm_api(patient_id, diagnosis_analysis.recommended_diagnoses)
                if success:
                    logger.info(f"Successfully pushed {len(diagnosis_analysis.recommended_diagnoses)} diagnoses for patient {patient_id}")
                    return True
                else:
                    logger.error(f"Failed to push diagnoses to Charm API for patient {patient_id}")
                    return False
            else:
                logger.info(f"No diagnoses recommended for patient {patient_id}")
                return True  # No diagnoses to push is considered success
                
        except Exception as e:
            import traceback
            logger.error(f"Error in push_diagnosis_to_charm for patient {patient_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _prepare_intake_for_diagnosis_analysis(self, intake_data: Dict[str, Any]) -> str:
        """Prepare intake data in a readable format for the diagnosis agent"""
        try:
            analysis_parts = []
            
            # Patient demographics
            demographics = intake_data.get("intake_demographics", {})
            if demographics:
                analysis_parts.append("PATIENT DEMOGRAPHICS:")
                analysis_parts.append(f"  Gender: {demographics.get('gender', 'Not specified')}")
                analysis_parts.append(f"  Date of Birth: {demographics.get('dateOfBirth', 'Not specified')}")
                analysis_parts.append("")
            
            # Weight and vitals
            weight_history = intake_data.get("intake_weight_history", {})
            if weight_history:
                analysis_parts.append("WEIGHT AND VITALS:")
                current_vitals = weight_history.get("currentVitals", {})
                height = current_vitals.get("height", {})
                weight = current_vitals.get("weight")
                
                if height and weight:
                    feet = height.get("feet", 0)
                    inches = height.get("inches", 0)
                    total_inches = (feet * 12) + inches
                    analysis_parts.append(f"  Height: {feet}' {inches}\" ({total_inches} inches)")
                    analysis_parts.append(f"  Weight: {weight} lbs")
                    
                    # Calculate BMI
                    if total_inches > 0 and weight > 0:
                        bmi = (weight / (total_inches ** 2)) * 703
                        analysis_parts.append(f"  Calculated BMI: {bmi:.1f}")
                
                # Weight history
                weight_hist = weight_history.get("weightHistory", {})
                if weight_hist:
                    analysis_parts.append(f"  Max weight ever: {weight_hist.get('maxEverWeighed', 'Not specified')} lbs")
                    analysis_parts.append(f"  Age at max weight: {weight_hist.get('ageAtMaxWeight', 'Not specified')}")
                
                # Bariatric surgery history
                bariatric = weight_history.get("bariatricSurgeryHistory", {})
                if bariatric.get("hasBariatricSurgeryHistory"):
                    analysis_parts.append(f"  Bariatric surgery history: Yes")
                    if bariatric.get("surgeryType"):
                        analysis_parts.append(f"    Surgery type: {bariatric['surgeryType']}")
                    if bariatric.get("surgeryYear"):
                        analysis_parts.append(f"    Surgery year: {bariatric['surgeryYear']}")
                
                analysis_parts.append("")
            
            # Medical history
            medical_history = intake_data.get("intake_medical_history", {})
            if medical_history:
                analysis_parts.append("MEDICAL HISTORY:")
                
                # Past medical history
                pmhx = medical_history.get("PMHx", [])
                pmhx_obesity = medical_history.get("PMHxObesityComorbid", [])
                all_conditions = (pmhx or []) + (pmhx_obesity or [])
                if all_conditions:
                    analysis_parts.append("  Past Medical History:")
                    for condition in all_conditions:
                        analysis_parts.append(f"    - {condition}")
                
                # Current medications
                medications = medical_history.get("currentMedications", [])
                if medications:
                    analysis_parts.append("  Current Medications:")
                    for med in medications:
                        med_name = med.get("medicationName", "Unknown")
                        strength = med.get("strength", "")
                        analysis_parts.append(f"    - {med_name} {strength}")
                
                # Specific conditions
                specific = medical_history.get("specificConditions", {})
                if specific:
                    if specific.get("pancreatitis", {}).get("hasPancreatitis"):
                        analysis_parts.append("  - Has history of pancreatitis")
                    if specific.get("gerdHeartburn", {}).get("hasGerd"):
                        analysis_parts.append("  - Has GERD/heartburn")
                
                # Family history
                family_history = medical_history.get("familyHistory", [])
                if family_history:
                    analysis_parts.append("  Family History:")
                    for fh in family_history:
                        member = fh.get("familyMember", "Unknown")
                        problem = fh.get("medicalProblem", "Unknown")
                        analysis_parts.append(f"    - {member}: {problem}")
                
                analysis_parts.append("")
            
            # Weight loss medication history
            if weight_history:
                wl_meds = weight_history.get("weightLossMedicationHistory", {})
                if wl_meds:
                    analysis_parts.append("WEIGHT LOSS MEDICATION HISTORY:")
                    glp1 = wl_meds.get("glp1Medications", {})
                    if glp1.get("hasTriedGlp1"):
                        analysis_parts.append("  Has tried GLP-1 medications:")
                        if glp1.get("tirzepatide", {}).get("hasTried"):
                            analysis_parts.append("    - Tirzepatide (Zepbound)")
                        if glp1.get("semaglutide", {}).get("hasTried"):
                            analysis_parts.append("    - Semaglutide")
                    analysis_parts.append("")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"Error preparing intake data for analysis: {e}")
            return str(intake_data)  # Fallback to raw data
    
    async def _push_diagnoses_to_charm_api(self, patient_id: str, diagnoses: List[DiagnosisRecommendation]) -> bool:
        """Push list of diagnoses to Charm Diagnosis API"""
        try:
            headers = await get_charm_api_headers()
            
            # Prepare diagnosis payload according to API spec
            diagnosis_payload = []
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for i, diagnosis in enumerate(diagnoses, 1):
                diagnosis_entry = {
                    "name": diagnosis.name,
                    "code": diagnosis.code,
                    "code_type": diagnosis.code_type,
                    "status": diagnosis.status,
                    "from_date": current_date,
                    "diagnosis_order": i
                }
                
                if diagnosis.comments:
                    diagnosis_entry["comments"] = diagnosis.comments
                
                diagnosis_payload.append(diagnosis_entry)
            
            # Make API call to add diagnoses
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/patients/{patient_id}/diagnoses",
                    json=diagnosis_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully pushed {len(diagnosis_payload)} diagnoses to Charm")
                    # Log each diagnosis that was added
                    for diag in diagnoses:
                        logger.info(f"  Added diagnosis: {diag.name} ({diag.code}) - {diag.reasoning}")
                    return True
                else:
                    logger.error(f"Failed to push diagnoses: {response.status_code} - {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Error pushing diagnoses to Charm API: {e}")
            return False


# Global service instance
ehr_service = EHRService()