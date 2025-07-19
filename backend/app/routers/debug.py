"""
Debug endpoints for testing individual components
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from app.services.ehr_service import ehr_service
from app.repositories.intake_repository import intake_repository
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/debug/health")
async def debug_health():
    """Basic health check"""
    return {"status": "ok", "message": "Debug endpoints working"}


@router.get("/debug/supabase")
async def debug_supabase():
    """Test Supabase connection"""
    try:
        client = get_supabase_client()
        # Try a simple query
        response = client.table("poc_intake_sessions").select("count", count="exact").execute()
        return {
            "status": "ok", 
            "message": "Supabase connection working",
            "session_count": response.count
        }
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/debug/ehr/{mrn}")
async def debug_ehr_validation(mrn: str):
    """Test EHR patient validation"""
    try:
        patient_data = await ehr_service.validate_patient_by_mrn(mrn)
        if patient_data:
            return {
                "status": "ok",
                "message": "Patient found",
                "patient_data": patient_data
            }
        else:
            return {
                "status": "not_found",
                "message": "Patient not found with provided MRN"
            }
    except Exception as e:
        logger.error(f"EHR validation failed for MRN {mrn}: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/debug/session-init/{mrn}")
async def debug_session_init(mrn: str):
    """Test session initialization step by step"""
    result = {"steps": [], "final_status": "unknown"}
    
    try:
        # Step 1: EHR validation
        result["steps"].append({"step": "ehr_validation", "status": "starting"})
        try:
            patient_data = await ehr_service.validate_patient_by_mrn(mrn)
            if patient_data:
                result["steps"][-1]["status"] = "success"
                result["steps"][-1]["data"] = patient_data
            else:
                result["steps"][-1]["status"] = "not_found"
                result["final_status"] = "patient_not_found"
                return result
        except Exception as e:
            result["steps"][-1]["status"] = "error"
            result["steps"][-1]["error"] = str(e)
            result["final_status"] = "ehr_error"
            return result
        
        # Step 2: Check existing session
        result["steps"].append({"step": "check_existing_session", "status": "starting"})
        try:
            existing_session = await intake_repository.get_session_by_mrn(mrn)
            result["steps"][-1]["status"] = "success"
            result["steps"][-1]["existing_session"] = existing_session is not None
            result["steps"][-1]["session_completed"] = existing_session.get("completed", False) if existing_session else False
        except Exception as e:
            result["steps"][-1]["status"] = "error"
            result["steps"][-1]["error"] = str(e)
            result["final_status"] = "database_error"
            return result
        
        # Step 3: Create new session if needed
        if not existing_session or existing_session.get("completed", False):
            result["steps"].append({"step": "create_new_session", "status": "starting"})
            try:
                session_id = await intake_repository.create_session(
                    charm_mrn=mrn,
                    initial_data={}
                )
                result["steps"][-1]["status"] = "success"
                result["steps"][-1]["session_id"] = session_id
                result["final_status"] = "success"
            except Exception as e:
                result["steps"][-1]["status"] = "error"
                result["steps"][-1]["error"] = str(e)
                result["final_status"] = "session_creation_error"
                return result
        else:
            result["final_status"] = "resumed_existing"
        
        return result
        
    except Exception as e:
        result["final_status"] = "unexpected_error"
        result["error"] = str(e)
        return result