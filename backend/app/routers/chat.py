"""
Chat API endpoints for the intake conversation
Now powered by Pydantic AI for type-safe, structured data collection
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.repositories.intake_repository import intake_repository
from app.repositories.chat_history_repository import chat_history_repository
from app.services.pydantic_intake_agent import pydantic_intake_agent, IntakeContext
from app.services.ehr_service import ehr_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _identify_missing_demographics_fields(demographics_data: Dict[str, Any]) -> List[str]:
    """
    Identify which required demographics fields are missing or empty
    """
    missing_fields = []
    
    # Check basic required fields
    if not demographics_data.get("firstName"):
        missing_fields.append("first_name")
    if not demographics_data.get("lastName"):
        missing_fields.append("last_name")
    if not demographics_data.get("email"):
        missing_fields.append("email")
    if not demographics_data.get("gender"):
        missing_fields.append("gender")
    if not demographics_data.get("dateOfBirth"):
        missing_fields.append("date_of_birth")
    
    # Check phone information
    phone_data = demographics_data.get("phone", {})
    if not phone_data.get("mobile"):
        missing_fields.append("mobile_phone")
    
    # Check address information
    address_data = demographics_data.get("address", {})
    if not address_data.get("addressLine1"):
        missing_fields.append("address_line1")
    if not address_data.get("city"):
        missing_fields.append("city")
    if not address_data.get("state"):
        missing_fields.append("state")
    if not address_data.get("zipCode"):
        missing_fields.append("zip_code")
    
    # Check emergency contact
    emergency_contact = demographics_data.get("emergencyContact")
    if not emergency_contact or not emergency_contact.get("name"):
        missing_fields.append("emergency_contact_name")
    if not emergency_contact or not emergency_contact.get("phone"):
        missing_fields.append("emergency_contact_phone")
    if not emergency_contact or not emergency_contact.get("relationship"):
        missing_fields.append("emergency_contact_relationship")
    
    return missing_fields


def _track_populated_field(data: Dict[str, Any], field_path: str, fields_answered: List[str]) -> None:
    """
    Helper function to track if a nested field has data and add it to fields_answered
    """
    try:
        # Navigate the nested path to check if field has data
        current = data
        parts = field_path.split('.')
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return  # Field doesn't exist or no data
        
        # If we got here and current has a value, add to fields_answered
        if current and current != "":
            fields_answered.append(field_path)
            
    except Exception:
        # Ignore errors in field checking
        pass


def _auto_handle_country_detection(updated_data: Dict[str, Any]) -> None:
    """
    Automatically set country to 'us' for US addresses, detect international formats
    """
    demographics = updated_data.get("intake_demographics", {})
    if not demographics:
        return
    
    address = demographics.get("address", {})
    if not address:
        return
    
    zip_code = address.get("zipCode", "")
    
    # If ZIP code is provided, check if it's international format
    if zip_code:
        if _is_international_address_format(zip_code):
            # Don't auto-set country for international addresses
            # Let the AI agent ask about it
            pass
        else:
            # Standard US ZIP code format, set country to US
            address["country"] = "us"
    else:
        # No ZIP code yet, assume US for now
        address["country"] = "us"


def _is_international_address_format(zip_code: str = "", address_parts: Dict[str, str] = None) -> bool:
    """
    Detect if address format suggests international location
    """
    if not zip_code:
        return False
    
    # Check for postal codes with letters (Canadian, UK, etc.)
    import re
    
    # Canadian postal code pattern (A1A 1A1)
    canadian_pattern = re.compile(r'^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$')
    
    # UK postal code patterns
    uk_pattern = re.compile(r'^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$')
    
    # Contains letters (not typical US ZIP)
    has_letters = re.search(r'[A-Za-z]', zip_code)
    
    if canadian_pattern.match(zip_code) or uk_pattern.match(zip_code) or has_letters:
        return True
    
    # Check for unusually long ZIP codes (more than 10 characters suggests international)
    if len(zip_code.replace('-', '').replace(' ', '')) > 10:
        return True
    
    return False


def _generate_post_verification_message(demographics_data: Dict[str, Any], missing_fields: List[str]) -> str:
    """
    Generate an intelligent message based on what EHR data we have and what's missing
    """
    # Start with verification acknowledgment
    first_name = demographics_data.get("firstName", "")
    base_message = f"Thank you for verifying your identity{', ' + first_name if first_name else ''}! "
    
    # Check what data we have from EHR
    has_basic_info = all([
        demographics_data.get("firstName"),
        demographics_data.get("lastName"), 
        demographics_data.get("email"),
        demographics_data.get("gender")
    ])
    
    has_phone = demographics_data.get("phone", {}).get("mobile")
    has_address = all([
        demographics_data.get("address", {}).get("addressLine1"),
        demographics_data.get("address", {}).get("city"),
        demographics_data.get("address", {}).get("state")
    ])
    
    # Generate contextual message based on available data
    if has_basic_info and has_phone and has_address:
        base_message += "I can see we have most of your contact information on file. "
    elif has_basic_info:
        base_message += "I can see we have your basic information on file. "
    else:
        base_message += "Let me help you complete your intake information. "
    
    # Ask about the first missing field
    if "mobile_phone" in missing_fields:
        return base_message + "To get started, what is your mobile phone number?"
    elif "address_line1" in missing_fields:
        return base_message + "I need to collect your address information. What is your street address?"
    elif "city" in missing_fields:
        return base_message + "What city do you live in?"
    elif "state" in missing_fields:
        return base_message + "What state do you live in?"
    elif "zip_code" in missing_fields:
        return base_message + "What is your ZIP code?"
    elif "emergency_contact_name" in missing_fields:
        return base_message + "For emergency contact information, who should we contact in case of an emergency?"
    elif "emergency_contact_phone" in missing_fields:
        return base_message + "What is your emergency contact's phone number?"
    elif "emergency_contact_relationship" in missing_fields:
        return base_message + "What is your emergency contact's relationship to you?"
    elif "email" in missing_fields:
        return base_message + "What is your email address?"
    elif "gender" in missing_fields:
        return base_message + "What is your gender?"
    else:
        # All required fields are present - confirm key details
        mobile = demographics_data.get("phone", {}).get("mobile", "")
        address = demographics_data.get("address", {}).get("addressLine1", "")
        
        if mobile and address:
            return base_message + f"I have all your required contact information. Let me confirm - your mobile number is {mobile} and your address is {address}. Is this correct?"
        elif mobile:
            return base_message + f"I have your contact information. Your mobile number is {mobile}. Let me also collect your address. What is your street address?"
        else:
            return base_message + "Let me start by collecting your contact information. What is your mobile phone number?"


async def _check_and_push_diagnoses_on_completion(session_id: str, updated_data: Dict[str, Any]) -> bool:
    """
    Check if the entire intake is completed and push diagnoses to Charm if so
    """
    try:
        # Check if the "completed" section indicates the intake is fully done
        completed_data = updated_data.get("completed", {})
        is_intake_complete = completed_data.get("isComplete", False)
        
        if not is_intake_complete:
            return False  # Intake not yet complete
        
        # Get session data for patient ID
        session_record = await intake_repository.verify_session(session_id)
        if not session_record or not session_record.get("charm_patient_id"):
            logger.error(f"No patient ID found for session {session_id}, cannot push diagnoses")
            return False
        
        patient_id = session_record["charm_patient_id"]
        
        # Get the complete intake data for diagnosis analysis
        complete_intake_data = session_record.get("intake", {})
        
        # Merge with the current updated data to ensure we have the latest information
        for key, value in updated_data.items():
            complete_intake_data[key] = value
        
        # Call the diagnosis function
        logger.info(f"Intake completed for session {session_id}, analyzing and pushing diagnoses for patient {patient_id}")
        success = await ehr_service.push_diagnosis_to_charm(patient_id, complete_intake_data)
        
        if success:
            logger.info(f"Successfully completed diagnosis analysis and push for patient {patient_id}")
            return True
        else:
            logger.error(f"Failed to complete diagnosis analysis and push for patient {patient_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking and pushing diagnoses on completion for session {session_id}: {e}")
        return False


async def _check_and_mark_section_complete(session_id: str, section_name: str, updated_data: Dict[str, Any]) -> bool:
    """
    Check if a section has been completed using the new tracking structure
    """
    try:
        tracking_key = f"{section_name}_tracking"
        tracking_data = updated_data.get(tracking_key, {})
        
        # Check if section is complete using the new tracking structure
        is_complete = tracking_data.get("isComplete", False)
        
        if is_complete:
            # Mark the section as complete in the database
            await intake_repository.mark_section_complete(session_id, section_name)
            logger.info(f"Automatically marked {section_name} as complete for session {session_id}")
            
            # Check if we should call Charm APIs to push data
            pushed_to_charm = tracking_data.get("pushed_to_charm", False)
            if not pushed_to_charm:
                # Get session data for Charm integration
                session_record = await intake_repository.verify_session(session_id)
                if session_record and session_record.get("charm_patient_id"):
                    patient_id = session_record["charm_patient_id"]
                    section_data = updated_data.get(section_name, {})
                    
                    # Map section names to types expected by ehr_service
                    section_type_map = {
                        "intake_demographics": "demographics",
                        "intake_medical_history": "medical_history",
                        "intake_weight_history": "weight_history",
                        "intake_insurance": "insurance"
                    }
                    
                    section_type = section_type_map.get(section_name)
                    if section_type:
                        # Call the new push_intake_section method
                        success = await ehr_service.push_intake_section(section_type, patient_id, section_data)
                        
                        if success:
                            # Update tracking to mark as pushed to Charm
                            tracking_data["pushed_to_charm"] = True
                            # Update the session with the new tracking data
                            updated_tracking = {f"{section_name}_tracking": tracking_data}
                            await intake_repository.update_session_intake(session_record["id"], updated_tracking)
                            logger.info(f"Successfully pushed {section_name} to Charm for patient {patient_id}")
                        else:
                            logger.error(f"Failed to push {section_name} to Charm for patient {patient_id}")
                    else:
                        logger.error(f"Unknown section name for Charm push: {section_name}")
                else:
                    logger.warning(f"No patient ID found for session {session_id}, cannot push to Charm")
            
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking section completion for {section_name} in session {session_id}: {e}")
        return False


class ChatMessage(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    current_section: str
    updated_data: Dict[str, Any] = {}
    agent_actions: List[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat_message(request: ChatMessage):
    """
    Process a chat message from the user using the LangChain agent
    """
    try:
        # Verify session exists and check confirmation status
        session_record = await intake_repository.verify_session(request.session_id)
        if not session_record:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        current_session = session_record.get("current_session", {})
        is_confirmed = current_session.get("confirmed", False)
        
        # If not confirmed, handle identity verification
        if not is_confirmed:
            # Handle identity verification flow
            verification_data = current_session.get("patient_data", {})
            stored_dob = verification_data.get("dob", "")
            stored_last_name = verification_data.get("last_name", "").lower()
            
            # Check verification attempt count
            verification_attempts = current_session.get("verification_attempts", 0)
            if verification_attempts >= 3:
                return ChatResponse(
                    response="I'm sorry, but we've reached the maximum number of verification attempts. Please call our office at 520-298-3300 to complete your registration and schedule your appointment.",
                    session_id=request.session_id,
                    current_section="verification_failed",
                    updated_data={},
                    agent_actions=["verification_limit_reached"]
                )
            
            # Get conversation history for context
            conversation_history = await chat_history_repository.get_recent_messages(request.session_id, count=6)
            
            # Use Pydantic AI to extract identity information with conversation context
            extracted = await pydantic_intake_agent.extract_identity(request.message, conversation_history)
            
            # Always attempt verification if we have any extracted information
            if extracted.last_name and extracted.date_of_birth:
                # Verify the information
                if (extracted.date_of_birth == stored_dob and 
                    extracted.last_name.lower() == stored_last_name):
                    
                    # Mark session as confirmed
                    await intake_repository.confirm_session(request.session_id)
                    
                    # Get the full patient data now that they're verified
                    patient_data = await ehr_service.validate_patient_by_mrn(session_record["charm_mrn"])
                    
                    # Store patient_id in session for future API calls
                    patient_id = patient_data.get("patient_id") if patient_data else None
                    if patient_id:
                        await intake_repository.update_session_data(request.session_id, {"charm_patient_id": patient_id})
                        logger.info(f"Stored patient_id {patient_id} for session {request.session_id}")
                    
                    # Populate demographics with EHR data
                    demographics_data = {
                        "patient_id":patient_id,
                        "record_id":session_record["charm_mrn"],
                        "firstName": patient_data.get("first_name", ""),
                        "lastName": patient_data.get("last_name", ""),
                        "dateOfBirth": patient_data.get("dob", ""),
                        "gender": patient_data.get("gender", ""),
                        "email": patient_data.get("email", ""),
                        "phone": {
                            "mobile": patient_data.get("mobile", ""),
                            "home": patient_data.get("home_phone", ""),
                            "work": patient_data.get("work_phone", ""),
                            "workExtension": patient_data.get("work_phone_extn", ""),
                            "preferred": "mobile" if patient_data.get("mobile") else ""
                        },
                        "address": {
                            "addressLine1": patient_data.get("address_line1", ""),
                            "addressLine2": patient_data.get("address_line2", ""),
                            "city": patient_data.get("city", ""),
                            "state": patient_data.get("state", ""),
                            "country": patient_data.get("country", "us"),
                            "zipCode": patient_data.get("postal_code", "")
                        },
                        "communicationPreferences": {
                            "preferredMethod": "",
                            "emailNotifications": patient_data.get("email_notification", "true") == "true",
                            "textNotifications": patient_data.get("text_notification", "true") == "true",
                            "voiceNotifications": patient_data.get("voice_notification", "true") == "true"
                        },
                        "maritalStatus": patient_data.get("marital_status", ""),
                        "employmentStatus": "",
                        "isComplete": False  # Always start as incomplete, even with EHR data
                    }
                    
                    # Create tracking data - initialize unasked_fields with all fields, then remove populated ones
                    from app.services.pydantic_intake_agent import _initialize_unasked_fields
                    unasked_fields = _initialize_unasked_fields("intake_demographics", demographics_data)
                    
                    # Create tracking object
                    tracking_data = {
                        "unasked_fields": unasked_fields,
                        "isComplete": False,
                        "pushed_to_charm": False
                    }
                    
                    # Complete data structure with tracking
                    complete_data = {
                        "intake_demographics": demographics_data,
                        "intake_demographics_tracking": tracking_data
                    }
                    
                    # Update the session with demographics data and tracking
                    await intake_repository.update_session_intake(session_record["id"], complete_data)
                    
                    # Generate intelligent response based on what data is missing
                    missing_fields = _identify_missing_demographics_fields(demographics_data)
                    response_message = _generate_post_verification_message(demographics_data, missing_fields)
                    
                    return ChatResponse(
                        response=response_message,
                        session_id=request.session_id,
                        current_section="intake_demographics",
                        updated_data=complete_data,
                        agent_actions=["identity_verified", "demographics_populated"]
                    )
                else:
                    # Information doesn't match - increment attempt count and provide feedback
                    new_attempt_count = verification_attempts + 1
                    
                    # Update session with new attempt count
                    await intake_repository.update_session_data(request.session_id, {"verification_attempts": new_attempt_count})
                    
                    # Format the date nicely for display
                    try:
                        from datetime import datetime as dt
                        parsed_date = dt.strptime(extracted.date_of_birth, "%Y-%m-%d")
                        formatted_date = parsed_date.strftime("%B %d, %Y")
                    except:
                        formatted_date = extracted.date_of_birth
                    
                    attempts_remaining = 3 - new_attempt_count
                    if attempts_remaining > 0:
                        feedback_msg = f"I'm using \"{extracted.last_name}\" and {formatted_date} for your date of birth and I'm not able to match you to an existing patient. Are these correct? You have {attempts_remaining} attempt{'s' if attempts_remaining != 1 else ''} remaining."
                    else:
                        feedback_msg = f"I'm using \"{extracted.last_name}\" and {formatted_date} for your date of birth and I'm not able to match you to an existing patient. This was your final attempt. Please call our office at 520-298-3300 to complete your registration."
                    
                    return ChatResponse(
                        response=feedback_msg,
                        session_id=request.session_id,
                        current_section="identity_verification",
                        updated_data={},
                        agent_actions=["verification_failed", "feedback_provided", f"attempt_{new_attempt_count}"]
                    )
            else:
                # No identity information extracted - increment attempt count
                new_attempt_count = verification_attempts + 1
                
                # Update session with new attempt count
                await intake_repository.update_session_data(request.session_id, {"verification_attempts": new_attempt_count})
                
                attempts_remaining = 3 - new_attempt_count
                if attempts_remaining > 0:
                    response_msg = f"I wasn't able to find your last name and date of birth in your message. Please provide both your **last name** and **date of birth** to verify your identity. You have {attempts_remaining} attempt{'s' if attempts_remaining != 1 else ''} remaining."
                else:
                    response_msg = "I wasn't able to find your last name and date of birth. This was your final attempt. Please call our office at 520-298-3300 to complete your registration."
                
                return ChatResponse(
                    response=response_msg,
                    session_id=request.session_id,
                    current_section="identity_verification",
                    updated_data={},
                    agent_actions=["awaiting_verification", f"attempt_{new_attempt_count}"]
                )
        
        # Session is confirmed, proceed with normal flow
        intake_data = session_record.get("intake", {})
        current_section = intake_repository.determine_current_section(intake_data)
        
        # Get patient data if available
        patient_data = None
        if session_record.get("charm_mrn"):
            try:
                patient_data = await ehr_service.validate_patient_by_mrn(session_record["charm_mrn"])
            except Exception as e:
                logger.warning(f"Could not retrieve patient data for session {request.session_id}: {e}")
        
        # Get conversation history from chat history table
        conversation_history = await chat_history_repository.get_recent_messages(request.session_id, count=40)
        
        # Create context for Pydantic AI agent
        context = IntakeContext(
            session_id=request.session_id,
            current_section=current_section,
            patient_data=patient_data,
            intake_data=intake_data,
            conversation_history=conversation_history
        )
        
        # Process message with Pydantic AI agent
        agent_response = await pydantic_intake_agent.process_conversation(request.message, context)
        
        # Update session with any new data
        if agent_response.updated_data:
            # Auto-detect and handle country setting for addresses
            _auto_handle_country_detection(agent_response.updated_data)
            
            await intake_repository.update_session_intake(session_record["id"], agent_response.updated_data)
            
            # Check if the current section should be marked as complete
            await _check_and_mark_section_complete(request.session_id, current_section, agent_response.updated_data)
            
            # Check if the entire intake is completed and push diagnoses if so
            await _check_and_push_diagnoses_on_completion(request.session_id, agent_response.updated_data)
            
        # Add new messages to chat history table
        now = datetime.utcnow().isoformat()
        user_message = {"role": "user", "content": request.message, "timestamp": now}
        assistant_message = {"role": "assistant", "content": agent_response.response, "timestamp": now}
        
        await chat_history_repository.add_messages(request.session_id, [user_message, assistant_message])
        
        return ChatResponse(
            response=agent_response.response,
            session_id=request.session_id,
            current_section=agent_response.current_section,
            updated_data=agent_response.updated_data,
            agent_actions=agent_response.agent_actions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message for session {request.session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing message"
        )


@router.get("/chat/{session_id}/summary")
async def get_conversation_summary(session_id: str):
    """Get a summary of the conversation for a session"""
    try:
        summary = await chat_history_repository.get_conversation_summary(session_id)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting conversation summary for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving conversation summary"
        )


@router.get("/chat/{session_id}/history")
async def get_conversation_history(session_id: str, limit: Optional[int] = None):
    """Get the full conversation history for a session"""
    try:
        history = await chat_history_repository.get_conversation_history(session_id, limit=limit)
        return {
            "session_id": session_id,
            "message_count": len(history),
            "messages": history
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving conversation history"
        )


@router.get("/chat/sections")
async def get_chat_sections():
    """Get available chat sections and their descriptions"""
    return {
        "sections": [
            {
                "name": "intake_demographics",
                "title": "Demographics",
                "description": "Personal information and contact details"
            },
            {
                "name": "intake_insurance", 
                "title": "Insurance Information",
                "description": "Insurance coverage and benefit details"
            },
            {
                "name": "intake_weight_history",
                "title": "Weight History",
                "description": "Weight management history and goals"
            },
            {
                "name": "intake_medical_history",
                "title": "Medical History", 
                "description": "Medical conditions, medications, and allergies"
            }
        ]
    }