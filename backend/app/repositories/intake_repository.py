"""
Repository layer for intake session data operations with Supabase
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import uuid4

from app.core.database import get_supabase_client
from app.models.intake_schemas import IntakeSession

logger = logging.getLogger(__name__)


class IntakeSessionRepository:
    """Repository for managing intake session data in Supabase"""
    
    def __init__(self):
        self.table_name = "poc_intake_sessions"
    
    def _get_client(self):
        """Get Supabase client"""
        return get_supabase_client()
    
    async def get_session_by_mrn(self, charm_mrn: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve intake session by patient MRN
        Returns the most recent session for the given MRN
        """
        try:
            response = self._get_client().table(self.table_name).select("*").eq("charm_mrn", charm_mrn).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session for MRN {charm_mrn}: {e}")
            raise
    
    async def create_session(self, charm_mrn: str, user_id: Optional[str] = None, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new intake session
        Returns the session_id (UUID)
        """
        try:
            now = datetime.utcnow().isoformat()
            
            session_data = {
                "charm_mrn": charm_mrn,
                "user_id": user_id,
                "intake": initial_data or {},
                "completed": False,
                "last_updated": now
            }
            
            response = self._get_client().table(self.table_name).insert(session_data).execute()
            
            if not response.data:
                raise Exception("Failed to create session")
            
            session_id = response.data[0]["id"]
            logger.info(f"Created new session {session_id} for MRN {charm_mrn}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session for MRN {charm_mrn}: {e}")
            raise
    
    async def update_session_intake(self, session_id: str, intake_data: Dict[str, Any]) -> bool:
        """
        Update the intake data for a session
        Merges new data with existing data
        """
        try:
            # First get the current session
            current_response = self._get_client().table(self.table_name).select("intake").eq("id", session_id).execute()
            
            if not current_response.data:
                raise Exception(f"Session {session_id} not found")
            
            # Merge the intake data
            current_intake = current_response.data[0].get("intake", {})
            current_intake.update(intake_data)
            
            # Update the session
            now = datetime.utcnow().isoformat()
            update_data = {
                "intake": current_intake,
                "last_updated": now
            }
            
            response = self._get_client().table(self.table_name).update(update_data).eq("id", session_id).execute()
            
            if not response.data:
                raise Exception("Failed to update session")
            
            logger.info(f"Updated session {session_id} with new intake data")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            raise
    
    async def update_session_section(self, session_id: str, section_name: str, section_data: Dict[str, Any]) -> bool:
        """
        Update a specific section of the intake data
        section_name should be one of: intake_demographics, intake_insurance, intake_weight_history, intake_medical_history
        """
        try:
            # Get current session
            current_response = self._get_client().table(self.table_name).select("intake").eq("id", session_id).execute()
            
            if not current_response.data:
                raise Exception(f"Session {session_id} not found")
            
            # Update the specific section
            current_intake = current_response.data[0].get("intake", {})
            current_intake[section_name] = section_data
            
            # Update the session
            now = datetime.utcnow().isoformat()
            update_data = {
                "intake": current_intake,
                "last_updated": now
            }
            
            response = self._get_client().table(self.table_name).update(update_data).eq("id", session_id).execute()
            
            if not response.data:
                raise Exception("Failed to update session section")
            
            logger.info(f"Updated session {session_id} section {section_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id} section {section_name}: {e}")
            raise
    
    async def complete_session(self, session_id: str, rating: Optional[float] = None, comments: Optional[str] = None) -> bool:
        """
        Mark a session as completed with optional rating and comments
        """
        try:
            now = datetime.utcnow().isoformat()
            update_data = {
                "completed": True,
                "last_updated": now
            }
            
            if rating is not None:
                update_data["star_ratings"] = rating
            
            if comments is not None:
                update_data["comments"] = comments
            
            response = self._get_client().table(self.table_name).update(update_data).eq("id", session_id).execute()
            
            if not response.data:
                raise Exception("Failed to complete session")
            
            logger.info(f"Completed session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing session {session_id}: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by session_id (UUID)"""
        try:
            response = self._get_client().table(self.table_name).select("*").eq("id", session_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            raise
    
    def determine_current_section(self, intake_data: Dict[str, Any]) -> str:
        """
        Determine which section the patient should continue with based on completed data
        Returns the next section to work on
        """
        sections = [
            "intake_demographics",
            "intake_insurance", 
            "intake_weight_history",
            "intake_medical_history"
        ]
        
        for section in sections:
            if section not in intake_data or not intake_data[section]:
                return section
        
        # All sections have some data, return the last one for completion
        return "completed"
    
    async def create_session_with_verification(self, charm_mrn: str, session_id: str, patient_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new intake session or add a new session to existing record
        Returns the main record ID
        """
        try:
            # Check if a record exists for this MRN
            existing = await self.get_session_by_mrn(charm_mrn)
            
            new_session_entry = {
                "session_id": session_id,
                "confirmed": False,
                "created_at": datetime.utcnow().isoformat(),
                "patient_data": patient_data  # Store for verification
            }
            
            if existing:
                # Add new session to existing sessions array
                sessions = existing.get("sessions", [])
                sessions.append(new_session_entry)
                
                update_data = {
                    "sessions": sessions,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                response = self._get_client().table(self.table_name).update(update_data).eq("id", existing["id"]).execute()
                
                if not response.data:
                    raise Exception("Failed to update sessions")
                
                logger.info(f"Added new session {session_id} to existing record for MRN {charm_mrn}")
                return existing["id"]
            else:
                # Create new record with first session
                session_data = {
                    "charm_mrn": charm_mrn,
                    "sessions": [new_session_entry],
                    "intake": {},
                    "completed": False,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                response = self._get_client().table(self.table_name).insert(session_data).execute()
                
                if not response.data:
                    raise Exception("Failed to create session record")
                
                record_id = response.data[0]["id"]
                logger.info(f"Created new record {record_id} with session {session_id} for MRN {charm_mrn}")
                return record_id
                
        except Exception as e:
            logger.error(f"Error creating/updating session for MRN {charm_mrn}: {e}")
            raise
    
    async def verify_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Find and verify if a session exists and get its confirmation status
        Returns the full record if found, None otherwise
        """
        try:
            # Search for records containing this session_id
            response = self._get_client().table(self.table_name).select("*").execute()
            
            for record in response.data:
                sessions = record.get("sessions", [])
                for session in sessions:
                    if session.get("session_id") == session_id:
                        # Found the session, return the record with session info
                        record["current_session"] = session
                        return record
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying session {session_id}: {e}")
            raise
    
    async def confirm_session(self, session_id: str) -> bool:
        """
        Mark a session as confirmed after identity verification
        """
        try:
            # Find the record containing this session
            record = await self.verify_session(session_id)
            if not record:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Update the session's confirmed status
            sessions = record.get("sessions", [])
            session_updated = False
            
            for session in sessions:
                if session.get("session_id") == session_id:
                    session["confirmed"] = True
                    session["confirmed_at"] = datetime.utcnow().isoformat()
                    session_updated = True
                    break
            
            if not session_updated:
                logger.error(f"Session {session_id} not found in sessions array")
                return False
            
            # Update the record
            update_data = {
                "sessions": sessions,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self._get_client().table(self.table_name).update(update_data).eq("id", record["id"]).execute()
            
            if not response.data:
                raise Exception("Failed to confirm session")
            
            logger.info(f"Confirmed session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming session {session_id}: {e}")
            raise


# Global repository instance
intake_repository = IntakeSessionRepository()