"""
EHR API service for patient validation and data operations
Uses the Charm Tracker API with token management
"""

import logging
from typing import Dict, List, Optional, Any

import httpx
from app.core.token_manager import get_charm_api_headers
from app.core.config import get_settings

logger = logging.getLogger(__name__)


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


# Global service instance
ehr_service = EHRService()