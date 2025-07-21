"""
Intake session management API endpoints
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.ehr_service import ehr_service
from app.repositories.intake_repository import intake_repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    print("DEBUG: test endpoint called")
    return {"message": "test endpoint works"}


class SessionInitRequest(BaseModel):
    mrn: str


class SessionResponse(BaseModel):
    session_id: str
    patient_data: Optional[Dict[str, Any]] = None
    current_section: str
    intake_data: Dict[str, Any]


@router.post("/sessions/init", response_model=SessionResponse)
async def initialize_session(request: SessionInitRequest = None):
    """
    Initialize a new intake session or resume existing one
    1. Validate patient MRN against EHR
    2. Check for existing session in Supabase
    3. Return session data and current progress
    """
    print("SESSIONS INIT CALLED - POST REQUEST RECEIVED")
    logger.info(f"DEBUG: initialize_session called with MRN: {request.mrn}")
    try:
        # Validate patient exists in EHR
        patient_data = await ehr_service.validate_patient_by_mrn(request.mrn)
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail="Patient not found with the provided MRN"
            )
        
        # Generate a new session ID
        from uuid import uuid4
        new_session_id = str(uuid4())
        
        logger.info(f"DEBUG: Creating new session {new_session_id} for MRN {request.mrn}")
        
        # Create or update the record with new unconfirmed session
        # Store minimal patient data for verification (DOB and last name)
        verification_data = {
            "dob": patient_data.get("dob"),
            "last_name": patient_data.get("last_name")
        }
        
        # Extract charm_patient_id from the EHR response
        charm_patient_id = patient_data.get("patient_id")
        
        record_id = await intake_repository.create_session_with_verification(
            request.mrn, 
            new_session_id, 
            verification_data, 
            charm_patient_id
        )
        
        logger.info(f"DEBUG: Created/updated record {record_id} with session {new_session_id}")
        
        # Don't populate demographics yet - wait for verification
        demographics_data = {
            "firstName": patient_data.get("first_name", ""),
            "lastName": patient_data.get("last_name", ""),
            "dateOfBirth": patient_data.get("dob", ""),  # Already in YYYY-MM-DD format
            "gender": patient_data.get("gender", ""),  # Empty if not provided
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
                "preferredMethod": "",  # Let chatbot determine based on conversation
                "emailNotifications": patient_data.get("email_notification", "true") == "true",
                "textNotifications": patient_data.get("text_notification", "true") == "true",
                "voiceNotifications": patient_data.get("voice_notification", "true") == "true"
            },
            "additionalInfo": {
                "language": patient_data.get("language", "") or "",  # Empty if not provided
                "maritalStatus": patient_data.get("marital_status", ""),
                "employmentStatus": ""  # Not provided in EHR data
            }
        }
        
        # Only set preferred communication method if explicitly provided
        if patient_data.get("preferred_communication") == "ChARM PHR":
            demographics_data["communicationPreferences"]["preferredMethod"] = "portal"
        elif patient_data.get("preferred_communication"):
            # Map other values if they exist
            pref_comm = patient_data.get("preferred_communication", "").lower()
            if "email" in pref_comm:
                demographics_data["communicationPreferences"]["preferredMethod"] = "email"
            elif "text" in pref_comm:
                demographics_data["communicationPreferences"]["preferredMethod"] = "text"
            elif "phone" in pref_comm:
                demographics_data["communicationPreferences"]["preferredMethod"] = "phone"
        
        # Return minimal data - session is not verified yet
        return SessionResponse(
            session_id=new_session_id,
            patient_data={"mrn": request.mrn},  # Only return MRN, not full patient data
            current_section="identity_verification",  # New section for verification
            intake_data={}  # Empty until verified
        )
            
    except Exception as e:
        logger.error(f"DEBUG: Exception occurred: {e}")
        logger.error(f"Error initializing session for MRN {request.mrn}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during session initialization"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session data by session ID""" 
    try:
        session_data = await intake_repository.get_session_by_id(session_id)
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        intake_data = session_data.get("intake", {})
        current_section = intake_repository.determine_current_section(intake_data)
        
        # Get patient data from EHR if available
        patient_data = None
        if session_data.get("charm_mrn"):
            try:
                patient_data = await ehr_service.validate_patient_by_mrn(session_data["charm_mrn"])
            except Exception as e:
                logger.warning(f"Could not retrieve patient data for session {session_id}: {e}")
        
        return SessionResponse(
            session_id=session_id,
            patient_data=patient_data,
            current_section=current_section,
            intake_data=intake_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving session"
        )


@router.put("/sessions/{session_id}/section")
async def update_session_section(
    session_id: str,
    section_name: str = Query(..., description="Section name to update"),
    section_data: Dict[str, Any] = None
):
    """Update a specific section of the intake data"""
    try:
        valid_sections = [
            "intake_demographics",
            "intake_insurance", 
            "intake_weight_history",
            "intake_medical_history"
        ]
        
        if section_name not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section name. Must be one of: {valid_sections}"
            )
        
        success = await intake_repository.update_session_section(
            session_id, section_name, section_data or {}
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update session section"
            )
        
        return {"message": f"Updated {section_name} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id} section {section_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error updating session"
        )


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    rating: Optional[float] = Query(None, ge=1, le=5),
    comments: Optional[str] = Query(None)
):
    """Mark session as completed with optional rating and comments"""
    try:
        success = await intake_repository.complete_session(
            session_id, rating, comments
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to complete session"
            )
        
        return {"message": "Session completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error completing session"
        )