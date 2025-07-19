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
from app.services.pydantic_intake_agent import pydantic_intake_agent, IntakeContext
from app.services.ehr_service import ehr_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


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
            
            # Use Pydantic AI to extract identity information
            extracted = await pydantic_intake_agent.extract_identity(request.message)
            
            # Check if we have high enough confidence and both pieces of info
            if extracted.confidence > 0.7 and extracted.last_name and extracted.date_of_birth:
                # Verify the information
                if (extracted.date_of_birth == stored_dob and 
                    extracted.last_name.lower() == stored_last_name):
                    
                    # Mark session as confirmed
                    await intake_repository.confirm_session(request.session_id)
                    
                    # Get the full patient data now that they're verified
                    patient_data = await ehr_service.validate_patient_by_mrn(session_record["charm_mrn"])
                    
                    # Populate demographics with EHR data
                    demographics_data = {
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
                        "additionalInfo": {
                            "language": patient_data.get("language", "") or "",
                            "maritalStatus": patient_data.get("marital_status", ""),
                            "employmentStatus": ""
                        }
                    }
                    
                    # Update the session with demographics data
                    await intake_repository.update_session_intake(session_record["id"], {"intake_demographics": demographics_data})
                    
                    return ChatResponse(
                        response="Thank you for verifying your identity. I can see we have some of your information on file. Let me help you complete your intake form. First, let me confirm your contact information.",
                        session_id=request.session_id,
                        current_section="intake_demographics",
                        updated_data={"intake_demographics": demographics_data},
                        agent_actions=["identity_verified", "demographics_populated"]
                    )
                else:
                    # Information doesn't match - provide feedback
                    feedback_msg = f"I'm using \"{extracted.last_name}\" and {extracted.original_date_format} for your date of birth and I'm not able to match you to an existing patient. Are these correct?"
                    
                    return ChatResponse(
                        response=feedback_msg,
                        session_id=request.session_id,
                        current_section="identity_verification",
                        updated_data={},
                        agent_actions=["verification_failed", "feedback_provided"]
                    )
            else:
                return ChatResponse(
                    response="**To get started, please enter your *last name* and *date of birth* to verify your identity.**",
                    session_id=request.session_id,
                    current_section="identity_verification",
                    updated_data={},
                    agent_actions=["awaiting_verification"]
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
        
        # Create context for Pydantic AI agent
        context = IntakeContext(
            session_id=request.session_id,
            current_section=current_section,
            patient_data=patient_data,
            intake_data=intake_data,
            conversation_history=session_record.get("conversation_history", [])
        )
        
        # Process message with Pydantic AI agent
        agent_response = await pydantic_intake_agent.process_conversation(request.message, context)
        
        # Update session with any new data
        if agent_response.updated_data:
            await intake_repository.update_session_intake(session_record["id"], agent_response.updated_data)
            
        # Update conversation history
        conversation_history = context.conversation_history.copy()
        conversation_history.append({"role": "user", "content": request.message})
        conversation_history.append({"role": "assistant", "content": agent_response.response})
        
        # Keep only last 20 exchanges
        if len(conversation_history) > 40:
            conversation_history = conversation_history[-40:]
            
        # Update session with conversation history
        await intake_repository.update_session_intake(session_record["id"], {"conversation_history": conversation_history})
        
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
        summary = await intake_agent.get_conversation_summary(session_id)
        return {"session_id": session_id, "summary": summary}
        
    except Exception as e:
        logger.error(f"Error getting conversation summary for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving conversation summary"
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