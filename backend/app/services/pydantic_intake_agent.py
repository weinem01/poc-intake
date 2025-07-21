"""
Pydantic AI-based intake agent for intelligent conversation management
Replaces LangChain with type-safe, structured data collection
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import httpx

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext # type: ignore
from pydantic_ai.models.openai import OpenAIModel

from app.core.config import get_settings
from app.core.token_manager import get_charm_api_headers
from app.models.intake_schemas import IntakeSession, IntakeDemographics, IntakeWeightHistory, IntakeMedicalHistory
from app.repositories.intake_repository import intake_repository

logger = logging.getLogger(__name__)


def _get_pydantic_schema_info(section_name: str) -> str:
    """
    Dynamically extract schema information from Pydantic models
    """
    # Map section names to their corresponding Pydantic models
    section_model_map = {
        "intake_demographics": IntakeDemographics,
        "intake_weight_history": IntakeWeightHistory,
        "intake_medical_history": IntakeMedicalHistory
    }
    
    model_class = section_model_map.get(section_name)
    if not model_class:
        return f"Unknown section: {section_name}"
    
    # Get the model's JSON schema
    schema = model_class.model_json_schema()
    
    # Extract field information in a readable format
    schema_info = f"Schema for {section_name}:\n"
    required_fields = schema.get("required", [])
    schema_info += _format_schema_properties(schema.get("properties", {}), required_fields, indent=0)
    
    return schema_info


def _format_schema_properties(properties: dict, required_fields: list = None, indent: int = 0) -> str: # type: ignore
    """
    Format schema properties into a readable structure for the AI agent
    """
    formatted = ""
    indent_str = "  " * indent
    required_fields = required_fields or []
    
    for field_name, field_info in properties.items():
        # Skip system fields
        if field_name in ["isComplete"]:
            continue
            
        field_type = field_info.get("type", "unknown")
        description = field_info.get("description", "")
        
        # Check if field is required
        is_required = field_name in required_fields
        required_marker = " (REQUIRED)" if is_required else " (optional)"
        
        # Handle different field types
        if field_type == "object":
            # Nested object - recurse into properties
            formatted += f"{indent_str}{field_name} (object){required_marker}:\n"
            nested_props = field_info.get("properties", {})
            nested_required = field_info.get("required", [])
            formatted += _format_schema_properties(nested_props, nested_required, indent + 1)
        elif field_type == "array":
            # Array field
            items = field_info.get("items", {})
            if "properties" in items:
                # Array of objects
                formatted += f"{indent_str}{field_name} (array of objects){required_marker}:\n"
                array_props = items.get("properties", {})
                array_required = items.get("required", [])
                formatted += _format_schema_properties(array_props, array_required, indent + 1)
            else:
                items_type = items.get("type", "unknown")
                formatted += f"{indent_str}{field_name} (array of {items_type}){required_marker}\n"
        else:
            # Simple field
            formatted += f"{indent_str}{field_name} ({field_type}){required_marker}\n"
        
        # Add description with AI Agent instructions
        if description:
            if "AI Agent:" in description:
                ai_instruction = description.split("AI Agent:")[-1].strip()
                formatted += f"{indent_str}  → {ai_instruction}\n"
            
    return formatted


def _get_all_field_paths(section_name: str) -> List[str]:
    """
    Get all possible field paths for a section (including nested fields)
    """
    section_model_map = {
        "intake_demographics": IntakeDemographics,
        "intake_weight_history": IntakeWeightHistory,
        "intake_medical_history": IntakeMedicalHistory
    }
    
    model_class = section_model_map.get(section_name)
    if not model_class:
        return []
    
    schema = model_class.model_json_schema()
    return _extract_field_paths(schema.get("properties", {}), "", schema)


def _get_field_question_groups(section_name: str) -> Dict[int, List[str]]:
    """
    Extract question groups from Pydantic model schema metadata
    Returns a dictionary mapping group numbers to lists of field paths
    """
    section_model_map = {
        "intake_demographics": IntakeDemographics,
        "intake_weight_history": IntakeWeightHistory,
        "intake_medical_history": IntakeMedicalHistory
    }
    
    model_class = section_model_map.get(section_name)
    if not model_class:
        return {}
    
    # Get the schema and extract group information
    groups = {}
    
    # Flattened grouping approach - all fields get simple sequential group numbers
    if section_name == "intake_demographics":
        groups = {
            1: ["firstName", "middleName", "lastName", "dateOfBirth", "gender"],
            2: ["email", "phone.mobile"],  # Essential contact info first
            3: ["phone.home", "phone.work", "phone.preferred"],  # Optional phone numbers
            4: ["address.addressLine1", "address.addressLine2", "address.city", "address.state", "address.zipCode"],
            5: ["emergencyContact.name", "emergencyContact.phone", "emergencyContact.relationship"],
            6: ["maritalStatus", "employmentStatus"],
            7: ["communicationPreferences.preferredMethod", "communicationPreferences.emailNotifications", "communicationPreferences.textNotifications", "communicationPreferences.voiceNotifications"],
            8: ["careTeamProviders"]
        }
    
    # Add other sections as needed
    elif section_name == "intake_weight_history":
        groups = {
            1: ["currentVitals.height.feet", "currentVitals.height.inches", "currentVitals.weight"],
            2: ["weightHistory.maxEverWeighed", "weightHistory.ageAtMaxWeight"],
            # Add more groups for weight history
        }
    elif section_name == "intake_medical_history":
        groups = {
            1: ["currentMedications", "allergies"],
            2: ["PMHx", "PMHxObesityComorbid"],
            # Add more groups for medical history
        }
    
    return groups


def _extract_field_paths_for_field(field_name: str, field_info, model_class) -> List[str]:
    """
    Extract all field paths for a given field (handles nested objects)
    """
    # Get the field alias if it exists
    alias = getattr(field_info, 'alias', None)
    base_field_name = alias if alias else field_name
    
    # Skip system fields
    if base_field_name == "isComplete":
        return []
    
    # Check if this is a nested model
    annotation = field_info.annotation
    
    # Handle Optional types
    if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
        # Get the non-None type from Optional
        args = annotation.__args__
        annotation = next((arg for arg in args if arg is not type(None)), annotation)
    
    # Handle List types  
    if hasattr(annotation, '__origin__') and annotation.__origin__ is list:
        # For now, treat lists as simple fields
        return [base_field_name]
    
    # Check if annotation is a BaseModel subclass
    if (hasattr(annotation, '__bases__') and 
        any(issubclass(base, BaseModel) for base in annotation.__bases__ if base is not object)):
        # This is a nested model - get all its field paths
        nested_paths = []
        for nested_field_name, nested_field_info in annotation.model_fields.items():
            nested_alias = getattr(nested_field_info, 'alias', None)
            nested_name = nested_alias if nested_alias else nested_field_name
            
            # Skip system fields
            if nested_name == "isComplete":
                continue
                
            nested_paths.append(f"{base_field_name}.{nested_name}")
        return nested_paths
    else:
        # Simple field
        return [base_field_name]


def _get_next_question_group_fields(unasked_fields: List[str], section_name: str) -> List[str]:
    """
    Get the fields for the next question group to ask about
    """
    question_groups = _get_field_question_groups(section_name)
    
    if not question_groups:
        # Fallback to single field if no groups defined
        return [unasked_fields[0]] if unasked_fields else []
    
    # Find the lowest numbered group that has unasked fields
    for group_num in sorted(question_groups.keys()):
        group_fields = question_groups[group_num]
        group_unasked = [field for field in group_fields if field in unasked_fields]
        
        if group_unasked:
            return group_unasked
    
    # No groups with unasked fields found
    return []


def _extract_field_paths(properties: dict, prefix: str = "", schema: dict = None) -> List[str]: # type: ignore
    """
    Recursively extract all field paths from schema properties
    """
    paths = []
    
    for field_name, field_info in properties.items():
        # Skip system fields
        if field_name in ["isComplete"]:
            continue
            
        current_path = f"{prefix}.{field_name}" if prefix else field_name
        
        # Handle $ref references
        if "$ref" in field_info:
            ref_path = field_info["$ref"]
            if ref_path.startswith("#/$defs/") and schema:
                def_name = ref_path.split("/")[-1]
                ref_definition = schema.get("$defs", {}).get(def_name, {})
                if ref_definition.get("type") == "object" and "properties" in ref_definition:
                    # Recursively extract from referenced definition
                    nested_paths = _extract_field_paths(ref_definition["properties"], current_path, schema)
                    paths.extend(nested_paths)
                else:
                    # Simple referenced type, add as field
                    paths.append(current_path)
            else:
                # Unknown reference, treat as simple field
                paths.append(current_path)
        elif "anyOf" in field_info:
            # Handle anyOf (like nullable fields)
            for any_option in field_info["anyOf"]:
                if "$ref" in any_option:
                    ref_path = any_option["$ref"]
                    if ref_path.startswith("#/$defs/") and schema:
                        def_name = ref_path.split("/")[-1]
                        ref_definition = schema.get("$defs", {}).get(def_name, {})
                        if ref_definition.get("type") == "object" and "properties" in ref_definition:
                            # Recursively extract from referenced definition
                            nested_paths = _extract_field_paths(ref_definition["properties"], current_path, schema)
                            paths.extend(nested_paths)
                            break
                elif any_option.get("type") == "array" and "items" in any_option:
                    items = any_option["items"]
                    if "$ref" in items:
                        ref_path = items["$ref"]
                        if ref_path.startswith("#/$defs/") and schema:
                            def_name = ref_path.split("/")[-1]
                            ref_definition = schema.get("$defs", {}).get(def_name, {})
                            if ref_definition.get("type") == "object" and "properties" in ref_definition:
                                # Array of objects - extract nested paths
                                nested_paths = _extract_field_paths(ref_definition["properties"], current_path, schema)
                                paths.extend(nested_paths)
                                break
            else:
                # No object found in anyOf, treat as simple field
                paths.append(current_path)
        else:
            field_type = field_info.get("type", "unknown")
            
            if field_type == "object":
                # Don't add the object itself, only its nested fields
                nested_props = field_info.get("properties", {})
                if nested_props:
                    nested_paths = _extract_field_paths(nested_props, current_path, schema)
                    paths.extend(nested_paths)
                else:
                    # If object has no properties, treat it as a simple field
                    paths.append(current_path)
            elif field_type == "array":
                # Check if array of objects with properties
                items = field_info.get("items", {})
                if "properties" in items:
                    nested_paths = _extract_field_paths(items["properties"], current_path, schema)
                    paths.extend(nested_paths)
                elif "$ref" in items:
                    ref_path = items["$ref"]
                    if ref_path.startswith("#/$defs/") and schema:
                        def_name = ref_path.split("/")[-1]
                        ref_definition = schema.get("$defs", {}).get(def_name, {})
                        if ref_definition.get("type") == "object" and "properties" in ref_definition:
                            # Array of objects - extract nested paths
                            nested_paths = _extract_field_paths(ref_definition["properties"], current_path, schema)
                            paths.extend(nested_paths)
                        else:
                            # Simple array, add as field
                            paths.append(current_path)
                    else:
                        paths.append(current_path)
                else:
                    # Simple array, add as field
                    paths.append(current_path)
            else:
                # Simple field
                paths.append(current_path)
    
    return paths


def _initialize_unasked_fields(section_name: str, existing_data: Dict[str, Any] = None) -> List[str]: # type: ignore
    """
    Initialize unasked_fields list with all fields from the Pydantic model
    Remove fields that already have data from EHR
    """
    # Get all field paths from the schema
    all_field_paths = _get_all_field_paths(section_name)
    
    # Remove system fields
    unasked_fields = [field for field in all_field_paths if "isComplete" not in field]
    
    # Debug logging to understand field generation
    logger.info(f"Schema field paths for {section_name}: {sorted(all_field_paths)}")
    logger.info(f"After removing system fields: {sorted(unasked_fields)}")
    
    # Remove fields that already have data from EHR
    if existing_data:
        # Check each field and log the decision
        fields_to_remove = []
        for field in unasked_fields:
            has_data = _field_has_data(existing_data, field)
            logger.info(f"Field '{field}': has_data={has_data}")
            if has_data:
                fields_to_remove.append(field)
        
        logger.info(f"Removing fields with data: {fields_to_remove}")
        unasked_fields = [field for field in unasked_fields 
                         if not _field_has_data(existing_data, field)]
    
    logger.info(f"Final unasked_fields for {section_name}: {sorted(unasked_fields)}")
    return unasked_fields


def _check_for_empty_fields(section_name: str, section_data: Dict[str, Any]) -> List[str]:
    """
    Check section data for empty fields and return list of field paths that are empty
    """
    all_field_paths = _get_all_field_paths(section_name)
    empty_fields = []
    
    for field_path in all_field_paths:
        if "isComplete" not in field_path and not _field_has_data(section_data, field_path):
            empty_fields.append(field_path)
    
    logger.info(f"Empty fields found in {section_name}: {sorted(empty_fields)}")
    return empty_fields


def _update_tracking_for_completeness(tracking_data: Dict[str, Any], section_name: str) -> Dict[str, Any]:
    """
    Update tracking data to check for section completeness
    """
    unasked_fields = tracking_data.get("unasked_fields", [])
    
    # Check if section should be marked complete (when no unasked fields remain)
    if len(unasked_fields) == 0:
        tracking_data["isComplete"] = True
        logger.info(f"Marked {section_name} as complete - all fields have been asked")
    else:
        tracking_data["isComplete"] = False
    
    return tracking_data


def _field_has_data(data: Dict[str, Any], field_path: str) -> bool:
    """
    Check if a nested field has meaningful data
    """
    try:
        current = data
        parts = field_path.split('.')
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        # Check if field has meaningful data
        if current is None or current == "":
            return False
        if isinstance(current, bool):
            return True  # Boolean values are always meaningful
        if isinstance(current, (list, dict)) and len(current) == 0:
            return False
            
        return True
        
    except Exception:
        return False


def _get_next_field_to_ask(unasked_fields: List[str]) -> Optional[str]:
    """
    Get the next field to ask from the unasked_fields list
    """
    return unasked_fields[0] if unasked_fields else None


def _group_related_fields(unasked_fields: List[str], current_section: str) -> List[List[str]]:
    """
    Group related fields together for efficient questioning
    
    Args:
        unasked_fields: List of fields that haven't been asked about
        current_section: Current intake section
    
    Returns:
        List of field groups that can be asked together
    """
    if not unasked_fields:
        return []
    
    # Define field groupings by section
    field_groups = {
        "intake_demographics": [
            # Name group
            ["firstName", "middleName", "lastName"],
            # Contact group
            ["email", "phone.mobile", "phone.home", "phone.work", "phone.preferred"],
            # Address group
            ["address.addressLine1", "address.addressLine2", "address.city", "address.state", "address.zipCode"],
            # Emergency contact group
            ["emergencyContact.name", "emergencyContact.phone", "emergencyContact.relationship"],
            # Personal info group
            ["maritalStatus", "employmentStatus"],
            # Communication preferences group
            ["communicationPreferences.preferredMethod", "communicationPreferences.emailNotifications", "communicationPreferences.textNotifications"],
            # Care team providers (handle separately due to search workflow)
            ["careTeamProviders"]
        ],
        "intake_weight_history": [
            # Current vitals group
            ["currentVitals.height.feet", "currentVitals.height.inches", "currentVitals.weight"],
            # Weight history group
            ["weightHistory.maxEverWeighed", "weightHistory.ageAtMaxWeight", "weightHistory.maxWeightLostByDieting"],
            # Diet history group
            ["dietHistory.pastDietsTried", "dietHistory.strugglesWithDiet"],
            # Eating patterns group
            ["dietHistory.typicalDayEating.breakfast", "dietHistory.typicalDayEating.lunch", "dietHistory.typicalDayEating.dinner", "dietHistory.typicalDayEating.beverages"],
            # Weight gain factors (can ask about multiple at once)
            ["dietHistory.weightGainFactors.genetics", "dietHistory.weightGainFactors.injuries", "dietHistory.weightGainFactors.chronicStressOrDepression"],
            # Exercise and treatment preferences
            ["exerciseInformation", "treatmentPreferences.treatmentApproach"],
            # Bariatric surgery group
            ["bariatricSurgeryHistory.hasBariatricSurgeryHistory", "bariatricSurgeryHistory.surgeryType", "bariatricSurgeryHistory.surgeryYear"],
            # GLP-1 medications group
            ["weightLossMedicationHistory.glp1Medications.hasTriedGlp1", "weightLossMedicationHistory.glp1Medications.tirzepatide", "weightLossMedicationHistory.glp1Medications.semaglutide"]
        ],
        "intake_medical_history": [
            # Medications and allergies group
            ["currentMedications", "allergies"],
            # Past medical history group
            ["PMHx", "PMHxObesityComorbid"],
            # Family history group
            ["familyHistory"],
            # Social history group (can group some together)
            ["socialHistory.smokingSummary", "socialHistory.alcoholSummary", "socialHistory.marijuanaSummary", "socialHistory.drugSummary"],
            # Employment and background group
            ["socialHistory.employmentStatus", "socialHistory.employmentDetails", "socialHistory.educationBackground", "socialHistory.financialSituation"],
            # Specific conditions group
            ["specificConditions.gerdHeartburn.hasGerd", "specificConditions.pancreatitis.hasPancreatitis"],
            # Past surgical history
            ["pastSurgicalHistory"]
        ]
    }
    
    section_groups = field_groups.get(current_section, [])
    result_groups = []
    
    # Find which groups have unasked fields
    for group in section_groups:
        group_unasked = [field for field in group if field in unasked_fields]
        if group_unasked:
            result_groups.append(group_unasked)
    
    # Add any remaining ungrouped fields individually
    all_grouped_fields = [field for group in result_groups for field in group]
    ungrouped = [field for field in unasked_fields if field not in all_grouped_fields]
    for field in ungrouped:
        result_groups.append([field])
    
    return result_groups


def _get_next_question_group(unasked_fields: List[str], current_section: str) -> List[str]:
    """
    Get the next group of related fields to ask about together
    """
    field_groups = _group_related_fields(unasked_fields, current_section)
    return field_groups[0] if field_groups else []


def _remove_field_from_unasked(unasked_fields: List[str], field_path: str) -> List[str]:
    """
    Remove a field from the unasked_fields list
    """
    return [field for field in unasked_fields if field != field_path]


def _deep_merge_dict(existing: dict, new: dict) -> dict:
    """
    Deep merge two dictionaries, with new values taking precedence
    """
    result = existing.copy()
    
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Both are dicts, merge recursively
            result[key] = _deep_merge_dict(result[key], value)
        elif isinstance(value, list) and key in result and isinstance(result[key], list):
            # Handle lists - for now, replace entirely to avoid duplicates
            # Could be enhanced to merge lists intelligently based on field type
            result[key] = value
        else:
            # Simple value or new key, use new value
            result[key] = value
    
    return result


class IdentityExtraction(BaseModel):
    """Model for extracting identity information from user input"""
    last_name: str = Field(description="Patient's last name extracted from the message")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD format")
    original_date_format: str = Field(description="The original date format found in the message")


class DemographicsUpdate(BaseModel):
    """Model for updating demographics information"""
    field_name: str = Field(description="The field being updated (e.g., 'email', 'phone.mobile')")
    new_value: str = Field(description="The new value for the field")


class SessionCompletion(BaseModel):
    """Model for session completion with rating and comments"""
    rating: int = Field(ge=1, le=5, description="Star rating from 1-5 for the intake experience")
    comments: Optional[str] = Field(default=None, description="Optional comments about the intake process")


class IntakeAgentResponse(BaseModel):
    """Structured response from the intake agent"""
    response: str = Field(description="The agent's response to the user")
    current_section: str = Field(description="Current section of the intake process")
    updated_data: Dict[str, Any] = Field(default_factory=dict, description="Any data updates to apply")
    agent_actions: List[str] = Field(default_factory=list, description="Actions taken by the agent")
    needs_followup: bool = Field(default=False, description="Whether additional information is needed")


class IntakeContext(BaseModel):
    """Context information for the intake conversation"""
    session_id: str
    current_section: str
    patient_data: Optional[Dict[str, Any]] = None
    intake_data: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


# Tool functions for the conversation agent
async def search_providers(provider_name: str, phone: str = None, practice_name: str = None, specialty: str = None) -> List[Dict[str, Any]]:  # type: ignore
    """
    Search for providers in Charm's referral directory
    
    Args:
        provider_name: Name of the provider to search for, remove any titles or suffixes (e.g., "Dr." "Doctor" "MD" "FNP" etc)
        phone: Provider's phone number (optional)
        practice_name: Name of the practice (optional) 
        specialty: Provider's specialty (optional)
    
    Returns:
        List of matching providers from Charm API
    """
    try:
        settings = get_settings()
        headers = await get_charm_api_headers()
        
        # Build search parameters
        params = {}
        
        # Split provider name into first and last name for better search
        name_parts = provider_name.strip().split()
        if len(name_parts) >= 2:
            params["first_name"] = name_parts[0]
            params["last_name"] = " ".join(name_parts[1:])
        else:
            params["last_name"] = provider_name
        
        if phone:
            # Remove formatting from phone number
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) >= 10:
                params["mobile"] = clean_phone
        
        if practice_name:
            params["practice_name"] = practice_name
            
        if specialty:
            params["speciality"] = specialty
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.charm_api_base_url}/settings/directory/providers",
                params=params,
                headers=headers,
                timeout=30.0
            )

            print (f"Here's the search response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0":
                    providers = data.get("providers", [])
                    logger.info(f"Found {len(providers)} providers matching search criteria")
                    return providers
                else:
                    logger.warning(f"Provider search returned non-zero code: {data}")
                    return []
            else:
                logger.error(f"Provider search failed: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error searching providers: {e}")
        return []


async def web_search_provider(provider_name: str, city: str = None, state: str = None, specialty: str = None) -> str: # type: ignore
    """
    Search the web for provider information using Perplexity API
    
    Args:
        provider_name: Name of the provider
        city: City to include in search (optional)
        state: State to include in search (optional) 
        specialty: Provider specialty to include in search (optional)
    
    Returns:
        String summary of web search results
    """
    try:
        settings = get_settings()
        perplexity_api_key = settings.get_perplexity_api_key()
        
        if not perplexity_api_key:
            logger.warning("Perplexity API key not found, falling back to manual verification")
            return f"Web search unavailable. Please gather provider information manually for {provider_name}."
        
        # Build search query
        search_terms = [f"Dr. {provider_name}" if not provider_name.lower().startswith('dr') else provider_name]
        if specialty:
            search_terms.append(specialty)
        if city and state:
            search_terms.extend([city, state])
        
        search_query = " ".join(search_terms)
        
        # Query Perplexity for provider information
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "user",
                    "content": f"Find contact information, practice details, and location for healthcare provider: {search_query}. Include practice name, phone number, address, specialty, and any other relevant professional details."
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if content:
                    logger.info(f"Web search completed for {provider_name}")
                    return f"Web search results for {provider_name}:\n\n{content}\n\nPlease verify this information with the patient before adding to their care team."
                else:
                    return f"Web search completed but no detailed information found for {provider_name}. Please gather provider information manually."
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return f"Web search failed for {provider_name}. Please gather provider information manually."
        
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return f"Unable to perform web search for {provider_name}. Please gather provider information manually."


async def add_provider_to_charm(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new provider to Charm's referral directory
    
    Args:
        provider_data: Provider information dictionary
    
    Returns:
        Dictionary with provider_id and success status
    """
    try:
        settings = get_settings()
        headers = await get_charm_api_headers()
        
        # Ensure required fields are present
        if not provider_data.get("first_name") or not provider_data.get("last_name"):
            return {"success": False, "error": "First name and last name are required"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.charm_api_base_url}/settings/directory/providers",
                json=provider_data,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0":
                    provider_details = data.get("provider_details", {})
                    provider_id = provider_details.get("provider_id")
                    logger.info(f"Successfully added provider with ID: {provider_id}")
                    return {
                        "success": True,
                        "provider_id": provider_id,
                        "provider_details": provider_details
                    }
                else:
                    logger.error(f"Add provider returned non-zero code: {data}")
                    return {"success": False, "error": f"API error: {data.get('message', 'Unknown error')}"}
            else:
                logger.error(f"Add provider failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
    except Exception as e:
        logger.error(f"Error adding provider: {e}")
        return {"success": False, "error": str(e)}


async def complete_intake_session(session_id: str, rating: int, comments: str = None) -> Dict[str, Any]: # type: ignore
    """
    Complete the intake session with rating and comments
    
    Args:
        session_id: The session ID to complete
        rating: Star rating from 1-5 for the intake experience
        comments: Optional comments about the intake process
    
    Returns:
        Dictionary with success status and any messages
    """
    try:
        # Validate rating
        if not 1 <= rating <= 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}
        
        # Call the repository to complete the session
        success = await intake_repository.complete_session(session_id, rating, comments)
        
        if success:
            logger.info(f"Successfully completed session {session_id} with rating {rating}")
            return {
                "success": True,
                "message": f"Thank you for your feedback! You rated your experience {rating}/5 stars."
            }
        else:
            logger.error(f"Failed to complete session {session_id}")
            return {"success": False, "error": "Failed to save completion data"}
            
    except Exception as e:
        logger.error(f"Error completing session {session_id}: {e}")
        return {"success": False, "error": str(e)}


class PydanticIntakeAgent:
    """
    Pydantic AI agent for managing patient intake conversations
    Provides type-safe, structured data collection with intelligent conversation flow
    """
    
    def __init__(self):
        settings = get_settings()
        # Set the API key in environment for OpenAI client
        import os
        os.environ['OPENAI_API_KEY'] = settings.get_openai_api_key()
        self.model = OpenAIModel('gpt-4o-mini')
        
        # Identity extraction agent
        self.identity_agent = Agent(
            self.model,
            result_type=IdentityExtraction,
            system_prompt="""
Extract Last Name & Date of Birth

Your sole job is to pull exactly two pieces of information—last_name and date_of_birth—out of the user’s current message (with conversation history used only as a fallback). Always return both fields, even if you’re not 100% certain.

1. Always return a JSON object with exactly these two keys:
{
  "last_name": "<your best guess as a single string>",
  "date_of_birth": "YYYY-MM-DD"
}
2. Priority: Current message over history
First, scan the current user message for both a name and a date.
Only if either piece is missing in the current message, look back at prior messages to fill that gap—but never overwrite what you found in the current message.

3. Extracting the Last Name
Look for any surname, family name, or standalone word that precedes the date.
If the user only supplies one word and it does not look like a month/day, treat that word as the last_name.
Always supply something as last_name—if you see no obvious surname, take the first word in the message.

4. Extracting the Date of Birth
Recognize these and similar formats:

MM/DD/YYYY or M/D/YY
MM-DD-YYYY
MonthName D, YYYY (e.g. July 29, 1872)
D MonthName YYYY
ISO-ish: YYYY-MM-DD
Normalize to four-digit year and zero-pad month/day → YYYY-MM-DD.

If you see multiple dates, choose the one that plausibly is a birthdate (past date, not today’s date).

5. When information is split across messages
If the current message has only one piece (e.g. it says “Patient” and the previous message said “July 29, 1872”), merge them.
But if the current message has both pieces, ignore history entirely.

6. Examples
Input	Output
Smith July 29, 1872	{ "last_name":"Smith","date_of_birth":"1872-07-29" }
Patton DOB: 3/5/90	{ "last_name":"Patton","date_of_birth":"1990-03-05" }
07-29-1872	{ "last_name":"07-29-1872","date_of_birth":"1872-07-29" } (fallback name → first token)
Hello, I’m Brown born 1/1/2000	{ "last_name":"Brown","date_of_birth":"2000-01-01" }

Follow these rules exactly. Always emit only the two-key JSON—no extra text.
            """
        )
        
        # Demographics collection agent
        self.demographics_agent = Agent(
            self.model,
            result_type=DemographicsUpdate,
            system_prompt="""
            You are a medical intake assistant collecting patient demographics.
            Extract specific demographic information updates from user messages.
            
            Focus on fields like:
            - Contact information (email, phone numbers)
            - Address details
            - Emergency contact
            - Communication preferences
            - Personal information (marital status, employment)
            
            Only extract information that is explicitly provided by the user.
            """
        )
        
        # Main conversation agent with tools
        self.conversation_agent = Agent(
            self.model,
            result_type=IntakeAgentResponse,
            system_prompt="""
            You are a friendly, empathetic medical-intake assistant.  
Use firstName only. Ask related questions together using bullet points for efficiency.
Ask 2-3 related questions from the same group to streamline the conversation.

Schema:
intake_demographics: {
  firstName, middleName?, lastName,
  email, mobilePhone, homePhone?, workPhone?,
  address: { addressLine1, city, state, zipCode, country="us" },
  emergencyContact: { name, relationship, phone },
  careTeamProviders: [ { providerName, phone?, practiceName?, specialty?, relationshipType?, isPrimaryCarePhysician? } ]
}
intake_weight_history: {
  currentHeight, currentWeight,
  maxWeight, ageAtMaxWeight,
  largestDietWeightLoss,
  dietHistory: [ { dietName, startDate?, endDate?, challenges? } ],
  mealPatterns, weightFactors, familyObesityHistory,
  exercise, treatmentPreferences,
  bariatricSurgeryHistory, glp1History
}
intake_medical_history: {
  medications: [ { name, dosage, frequency } ],
  allergies,
  diagnosedConditions,
  socialHistory: { smoking?, alcohol?, otherSubstances? },
  familyMedicalHistory,
  surgicalHistory: [ { procedureName, approximateYear } ]
}

CRITICAL:
- On every turn, load the prior `updated_data` state.
- Parse the user message and merge any newly provided values into that state.
- Always return the **entire** `updated_data` object (including previously collected fields) before asking your next question.
- If the user corrects or references past data (“you forgot X”), re-emit that field in `updated_data` to confirm it’s saved.

Loop (per turn):
1. Identify the next group of missing fields in `current_section`.
2. Ask 2-3 related questions from that group using bullet points.
3. If section complete → respond "✅ {section} complete. Moving to {next_section}."
4. Repeat until all sections done; then ask for star rating + comments.

Provider sub-flow:
1. Ask “What’s your provider’s name?” → call `search_providers(name)`
2. If matches → present list & confirm → store `provider_id` → ask “Any more providers?”
3. Else ask “What’s their phone?” → `search_providers(name, phone)` → confirm or…
4. Else ask “Practice name?” → `search_providers(name, phone, practiceName)` or fallback to `web_search_provider` → confirm → `add_provider_to_charm`

Tools:
search_providers, web_search_provider, add_provider_to_charm, complete_intake_session

Response format (JSON):
```json
{
  "response": "...?",
  "current_section": "...",
  "updated_data": { /* full state with all collected fields */ },
  "agent_actions": [ /* e.g. "extracted_address", "merged_state" */ ]
}


            # You are a friendly, professional medical intake assistant for Pound of Cure Weight Loss clinic.
            
            # Your role is to:
            # 1. Guide patients through their intake form completion
            # 2. Ask relevant follow-up questions for missing information
            # 3. Confirm and validate information provided
            # 4. Extract and structure data from user responses
            # 5. Maintain a conversational, empathetic tone, addressing the user by their first name (first_name), do not address the user by their middle name.
            # 6. Be sure to end any message with a question to keep the conversation going
            # 7. Handle care team provider searches and additions using available tools
            
            # CRITICAL: When users provide information, you MUST extract it and return it in the updated_data field.
            # YOU MUST ALWAYS EXTRACT DATA FROM USER RESPONSES. DO NOT IGNORE ANY PROVIDED INFORMATION.
            
            # Current intake sections (insurance is temporarily disabled):
            # - intake_demographics: Basic patient information (contact info, address, emergency contact, care team providers)
            # - intake_weight_history: Weight and diet history
            # - intake_medical_history: Medical conditions, medications, allergies
            
            # CARE TEAM PROVIDER WORKFLOW:
            # When collecting care team provider information, follow this progressive search approach:
            
            # 1. **Start with name only**: Ask "What is your provider's name?" 
            # 2. **Search by name**: Use search_providers tool with just the provider name
            # 3. **If results found**: Present them to user for confirmation
            # 4. **If no suitable results**: Ask "What is their phone number?" and search again with name + phone
            # 5. **If still no suitable results**: Ask "What is the name of their practice or clinic?" and search with name + phone + practice
            # 6. **If still no suitable results**: Use web_search_provider tool with all available information
            # 7. **Present web search results**: Show findings to user and ask for confirmation
            # 8. **If user confirms**: Use add_provider_to_charm tool to add the new provider
            # 9. **Store provider_id**: Save the provider_id in careTeamProviders data
            # 10. **Ask for more**: "Do you have any other healthcare providers you'd like to add?"
            
            # IMPORTANT SEARCH STRATEGY:
            # - Always search with minimal information first (just name)
            # - Only ask for additional details if no suitable matches are found
            # - Present ANY found providers to the user for confirmation before asking for more details
            # - Use progressive disclosure - don't overwhelm the user with multiple questions at once
            # - When presenting search results, show provider name, practice, specialty, and location if available
            
            # Available Tools:
            # - search_providers(provider_name, phone=None, practice_name=None, specialty=None): Search existing providers
            # - web_search_provider(provider_name, city=None, state=None, specialty=None): Web search for provider info
            # - add_provider_to_charm(provider_data): Add new provider to Charm directory
            # - complete_intake_session(session_id, rating, comments=None): Complete the session with rating and comments
            
            # Data Extraction Rules:
            # - When user provides address information, parse it into addressLine1, city, state, zipCode
            # - Example: "3010 E Camino Juan Paisano, Tucson AZ 85718" becomes:
            #   addressLine1: "3010 E Camino Juan Paisano", city: "Tucson", state: "AZ", zipCode: "85718"
            # - When user provides phone numbers, extract mobile, home, work
            # - When user provides emergency contact info, extract name, phone, relationship
            # - For care team providers: extract providerName, phone, practiceName, specialty, relationshipType, isPrimaryCarePhysician
            # - Always set country to "us" unless ZIP code suggests international format
            # - Return ALL extracted data in the updated_data field with proper nesting
            # - When storing data in the schema, convert any statements into third person
            
            # Response Structure:
            # - response: Your conversational message to the user
            # - current_section: The current intake section being worked on
            # - updated_data: MUST contain any data extracted from user's message, properly nested
            # - agent_actions: List actions taken (e.g., "extracted_address", "searched_provider", "added_provider")
            
            # CONVERSATION STRATEGY - GROUPED QUESTIONS:
            
            # DEMOGRAPHICS (ask related fields together):
            # Group 2 - Contact Info: "I need your contact information:
            #   • What's your email address?
            #   • What's your mobile phone number?
            #   • Do you have a work or home phone number?"
            # Group 3 - Address: "Now I need your home address:
            #   • What's your street address?
            #   • What city and state do you live in?
            #   • What's your ZIP code?"
            # Group 4 - Emergency Contact: "For emergency contact information:
            #   • Who should we contact in an emergency?
            #   • What's their phone number?
            #   • What's their relationship to you?"
            
            # WEIGHT HISTORY:
            # - Vitals: "What's your current height and weight?"
            # - Weight History: "What's the most you've ever weighed, at what age?"
            # - Weight Loss History: "What's the most weight you've lost through dieting? In the last few years, what diets have you tried and what struggles have you faced?"
            # - Diet Patterns: "What do you typically eat for breakfast, lunch, and dinner? What about beverages and snacks throughout the day?"
            # - Weight Factors: "Have medications, injuries, or stress contributed to your weight gain? Tell me about any factors that have affected your weight."
            # - Obesity Family History: "Does anyone in your family have a history of obesity? Which side of the family?"
            # - Weight Factors - Female, only ask if female gender, "Has pregnancy or menopause affected your weight?"
            # - Exercise: "What types of exercise do you currently do? How often?"
            # - Treatment Preferences: "What treatment approach are you most interested in? Do you prefer medication, lifestyle changes or Bariatric Surgery, or a combination?"
            # - Bariatric Surgery: "Have you had any bariatric surgery in the past? If so, what type and when?"
            # - GLP-1 Medications: "Have you tried any GLP-1 medications like semaglutide or tirzepatide? If so, which ones and when?"
            # - GLP-1 Medications detailed if they have tried in the past: "What was the highest dose you took? How long did you take it? Did you experience any side effects? How much weight did you lose?"

            # MEDICAL HISTORY:
            # - Medications & Allergies: "What medications are you currently taking? Please include names, dosages, and directions. Also, do you have any allergies to medications or foods?"
            # - Medical Conditions: "What medical conditions have you been diagnosed with? This includes both general conditions and any weight-related health issues."
            # - Are there any other medical conditions that you have been diagnosed with that are related to your weight like diabetes, high blood pressure, sleep apnea, high cholesterol? Others?"
            # - Social History: "Tell me about your smoking history, have you ever smoked? Do you currently smoke?"
            # - Alcohol Use: "How much alcohol do you drink in an average week? Do you use Marijuana?"
            # - Illegal Drug Use: "Do you have any history of illegal drug use? When was the last time you used?"
            # - Family History: "What medical conditions run in your family? 
            # - Surgical History: "Have you had any surgeries in the past? Make sure to include all abdominal surgeries. List them and give the approximate year they were performed."

            
            # EXTRACTION STRATEGY:
            # - Always extract ALL information provided in a response, even if not directly asked
            # - If user provides address as "123 Main St, Phoenix AZ 85001", extract: addressLine1, city, state, zipCode
            # - If user says "My PCP is Dr. Smith at Phoenix Medical", extract: providerName, practiceName, relationshipType
            # - Parse comprehensive responses and populate multiple fields simultaneously
            # - Don't ask for information already provided in previous responses
            # - If there is significant ambiguity, ask clarifying questions to ensure accuracy
            
            # Guidelines:
            # - Ask 2-3 related questions from the same group using bullet points
            # - Extract every piece of information from user responses
            # - Be specific about what information you need
            # - Move through question groups systematically
            # - When a section is complete, acknowledge completion and transition to the next section
            # - Use natural, conversational language
            # - Show empathy for sensitive topics (weight, medical conditions)
            # - Focus on the next group of related fields in the current section
            # - If you detect that all required fields in a section are complete, mention this to the user
            # - For addresses: assume US location, set country to "us" automatically
            # - Only ask about country if ZIP/postal code contains letters or unusual format suggesting international address
            # - When all fields are complete, make sure to collect a star rating (1-5) rating their experience with the intake process compared to traditional doctor's office forms and any comments about the process they have.
            
            # CARE TEAM PROVIDER SPECIFIC GUIDELINES:
            # - Start with ONLY the provider name - don't ask for phone/practice initially
            # - Search immediately after getting the name - don't wait to collect more info
            # - If search returns results, present them clearly: "I found these providers in our directory: [list with name, practice, specialty]. Is one of these your provider?"
            # - Only ask for phone number if name search returns no suitable matches
            # - Only ask for practice name if name + phone search returns no suitable matches
            # - Always confirm provider details with the user before adding to avoid mistakes
            # - Use progressive disclosure - reveal search strategy step by step, don't explain the whole process upfront
            """,
            tools=[search_providers, web_search_provider, add_provider_to_charm] # type: ignore
        )
    
    async def extract_identity(self, message: str, conversation_history: List[Dict[str, str]] = None) -> IdentityExtraction: # type: ignore
        """Extract identity information from user message and conversation history"""
        try:
            # Build context with message and recent history
            context = f"Current message: {message}\n"
            if conversation_history:
                context += "Recent conversation history:\n"
                for entry in conversation_history[-3:]:  # Last 3 messages
                    role = entry.get("role", "unknown")
                    content = entry.get("content", "")
                    context += f"{role}: {content}\n"
            
            result = await self.identity_agent.run(context)
            return result.data
        except Exception as e:
            logger.error(f"Error extracting identity: {e}")
            return IdentityExtraction(
                last_name="",
                date_of_birth="",
                original_date_format=""
            )
    
    async def process_demographics_update(self, message: str, context: IntakeContext) -> DemographicsUpdate:
        """Process demographic information updates from user message"""
        try:
            prompt = f"""
            Current demographics data: {context.intake_data.get('intake_demographics', {})}
            User message: {message}
            
            Extract any demographic information updates from the user's message.
            """
            result = await self.demographics_agent.run(prompt)
            return result.data
        except Exception as e:
            logger.error(f"Error processing demographics update: {e}")
            return DemographicsUpdate(
                field_name="",
                new_value=""
            )
    
    async def process_conversation(self, message: str, context: IntakeContext) -> IntakeAgentResponse:
        """Process the main intake conversation"""
        try:
            # Build conversation prompt with context
            current_data = context.intake_data.get(context.current_section, {})
            tracking_key = f"{context.current_section}_tracking"
            tracking_data = context.intake_data.get(tracking_key, {})
            
            # Initialize tracking data if not present
            if "unasked_fields" not in tracking_data:
                tracking_data["unasked_fields"] = _initialize_unasked_fields(context.current_section, current_data)
            if "isComplete" not in tracking_data:
                tracking_data["isComplete"] = False
            if "pushed_to_charm" not in tracking_data:
                tracking_data["pushed_to_charm"] = False
            
            unasked_fields = tracking_data.get("unasked_fields", [])
            
            # Get dynamic schema information for the current section
            schema_info = _get_pydantic_schema_info(context.current_section)
            
            # Determine what group of fields to ask about next (grouped question approach)
            next_question_group = _get_next_question_group_fields(unasked_fields, context.current_section)
            
            prompt = f"""
            Session ID: {context.session_id}
            Current Section: {context.current_section}
            
            {schema_info}
            
            Current Section Data: {current_data}
            
            FIELD TRACKING:
            Unasked fields remaining: {unasked_fields}
            Next question group to ask about: {next_question_group}
            Total remaining fields: {len(unasked_fields)}
            
            Conversation History:
            {self._format_conversation_history(context.conversation_history)}
            
            User Message: "{message}"
            
            CRITICAL DATA EXTRACTION REQUIREMENTS:
            1. You MUST extract data from the user's message into the updated_data field
            2. NEVER say you've saved data unless you actually extract it
            3. Use the schema above to understand the exact field structure for {context.current_section}
            4. ALWAYS parse the user's message for any information that matches schema fields
            5. Extract EVERY piece of information provided, even if not directly asked
            6. Map extracted data to exact schema field names (e.g., middleName, email, phone.work)
            7. Return ALL extracted data in the updated_data field with proper nesting
            8. Use this exact format: updated_data should contain {context.current_section} as the top level
            9. ALSO include tracking data in {tracking_key} with updated unasked_fields list
            10. Remove any field you extracted data for from the unasked_fields list
            11. Ask about the NEXT GROUP of related fields from next_question_group using bullet points
            12. Provide a conversational response acknowledging what you collected
            
            EXAMPLE DATA EXTRACTION:
            If user says "3010 E Camino Juan Paisano":
            - Extract address.addressLine1: "3010 E Camino Juan Paisano"
            - Remove "address.addressLine1" from unasked_fields
            
            If user says "drweiner@gmail.com":
            - Extract email: "drweiner@gmail.com" 
            - Remove "email" from unasked_fields
            
            If user says "Jeremy, matthew.weiner@poundofcureweightloss.com, work is 5202983300":
            - Extract middleName: "Jeremy"
            - Extract email: "matthew.weiner@poundofcureweightloss.com"  
            - Extract phone.work: "5202983300"
            - Remove these fields from unasked_fields: ["middleName", "email", "phone.work"]
            
            TRACKING FORMAT:
            "updated_data": {{
                "{context.current_section}": {{ /* actual data */ }},
                "{tracking_key}": {{
                    "unasked_fields": ["remaining", "field", "paths"],
                    "isComplete": false,
                    "pushed_to_charm": false
                }}
            }}
            
            CRITICAL: Always remove fields from unasked_fields when you ask about them or collect data for them.
            """
            
            result = await self.conversation_agent.run(prompt)
            agent_response = result.data
            
            # Merge new data with existing data
            if agent_response.updated_data:
                merged_data = self._merge_intake_data(
                    existing_data=context.intake_data,
                    new_data=agent_response.updated_data,
                    current_section=context.current_section
                )
                # Update the response with merged data
                agent_response.updated_data = merged_data
            
            return agent_response
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return IntakeAgentResponse(
                response="I apologize, but I'm having trouble processing your message. Could you please try again?",
                current_section=context.current_section,
                updated_data={},
                agent_actions=["error_recovery"],
                needs_followup=True
            )
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for context"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        for entry in history[-5:]:  # Last 5 exchanges
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)
    
    def _merge_intake_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any], current_section: str) -> Dict[str, Any]:
        """
        Merge new intake data with existing data, handling conflicts intelligently
        """
        try:
            # Start with existing data as base
            merged_data = existing_data.copy()
            
            # Get the section-specific data from new_data
            new_section_data = new_data.get(current_section, {})
            
            if new_section_data:
                # Get existing section data
                existing_section_data = merged_data.get(current_section, {})
                
                # Deep merge the section data
                merged_section_data = _deep_merge_dict(existing_section_data, new_section_data)
                
                # Update the merged data with the new section
                merged_data[current_section] = merged_section_data
                
                logger.debug(f"Merged data for {current_section}: existing={existing_section_data}, new={new_section_data}, merged={merged_section_data}")
            
            # Merge tracking data if present
            tracking_key = f"{current_section}_tracking"
            new_tracking_data = new_data.get(tracking_key, {})
            
            if new_tracking_data:
                existing_tracking_data = merged_data.get(tracking_key, {
                    "unasked_fields": [],
                    "isComplete": False,
                    "pushed_to_charm": False
                })
                
                # Use the updated unasked_fields from new data
                merged_tracking = {
                    "unasked_fields": new_tracking_data.get("unasked_fields", existing_tracking_data.get("unasked_fields", [])),
                    "isComplete": new_tracking_data.get("isComplete", existing_tracking_data.get("isComplete", False)),
                    "pushed_to_charm": new_tracking_data.get("pushed_to_charm", existing_tracking_data.get("pushed_to_charm", False))
                }
                
                # Check for completeness
                merged_tracking = _update_tracking_for_completeness(merged_tracking, current_section)
                
                merged_data[tracking_key] = merged_tracking
                
                logger.debug(f"Merged tracking for {current_section}: {merged_tracking}")
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging intake data: {e}")
            # Fallback to just returning new data if merge fails
            return new_data
    
    async def determine_next_section(self, current_data: Dict[str, Any]) -> str:
        """Determine the next section based on current intake data completion"""
        return intake_repository.determine_current_section(current_data)


# Global agent instance
pydantic_intake_agent = PydanticIntakeAgent()