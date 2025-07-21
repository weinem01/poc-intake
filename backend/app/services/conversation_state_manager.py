"""
Conversation State Manager
=========================

Server-side in-memory state management for conversation flow.
Eliminates race conditions and improves performance.
"""

import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timedelta

from app.services.pydantic_intake_agent import _get_all_field_paths, _field_has_data

logger = logging.getLogger(__name__)


class SessionState:
    """State for a single conversation session"""
    
    def __init__(self, session_id: str, current_section: str):
        self.session_id = session_id
        self.current_section = current_section
        self.unasked_fields: List[str] = []
        self.asked_this_turn: List[str] = []
        self.last_updated = datetime.utcnow()
        self.initialized = False
    
    def mark_fields_asked(self, fields: List[str]):
        """Mark fields as asked (remove from unasked_fields)"""
        for field in fields:
            if field in self.unasked_fields:
                self.unasked_fields.remove(field)
                self.asked_this_turn.append(field)
        self.last_updated = datetime.utcnow()
        logger.info(f"Session {self.session_id}: marked fields as asked: {fields}")
        logger.info(f"Session {self.session_id}: remaining unasked fields: {len(self.unasked_fields)}")
    
    def get_next_questions(self, count: int = 3) -> List[str]:
        """Get next 2-3 questions to ask"""
        return self.unasked_fields[:count]
    
    def is_section_complete(self) -> bool:
        """Check if current section has no more questions"""
        return len(self.unasked_fields) == 0
    
    def reset_for_new_section(self, new_section: str):
        """Reset state for a new section"""
        self.current_section = new_section
        self.unasked_fields = _get_all_field_paths(new_section)
        self.asked_this_turn = []
        self.last_updated = datetime.utcnow()
        self.initialized = False
        logger.info(f"Session {self.session_id}: reset for section {new_section}, {len(self.unasked_fields)} fields to ask")


class ConversationStateManager:
    """Manages conversation state in memory for all sessions"""
    
    def __init__(self):
        self.session_states: Dict[str, SessionState] = {}
        self.cleanup_interval = timedelta(hours=2)  # Clean up old sessions
    
    async def initialize_session(self, session_id: str, current_section: str, 
                                existing_intake_data: Dict[str, Any], 
                                verification_data: Dict[str, Any]) -> SessionState:
        """
        Initialize session state by reading existing data and removing populated fields
        """
        # Create or get session state
        if session_id not in self.session_states:
            self.session_states[session_id] = SessionState(session_id, current_section)
        
        state = self.session_states[session_id]
        
        # Start with all possible fields for the section
        all_fields = _get_all_field_paths(current_section)
        state.unasked_fields = all_fields.copy()
        
        logger.info(f"Session {session_id}: initializing with {len(all_fields)} total fields for {current_section}")
        
        # Remove fields that already have data from intake (database)
        section_data = existing_intake_data.get(current_section, {})
        if section_data:
            fields_with_data = self._find_populated_fields(section_data, all_fields)
            for field in fields_with_data:
                if field in state.unasked_fields:
                    state.unasked_fields.remove(field)
            logger.info(f"Session {session_id}: removed {len(fields_with_data)} fields from intake data: {fields_with_data}")
        
        # Remove fields that have data from verification process (EHR data)
        if verification_data:
            verification_fields = self._map_verification_to_fields(verification_data, current_section)
            for field in verification_fields:
                if field in state.unasked_fields:
                    state.unasked_fields.remove(field)
            logger.info(f"Session {session_id}: removed {len(verification_fields)} fields from verification data: {verification_fields}")
        
        state.initialized = True
        state.last_updated = datetime.utcnow()
        
        logger.info(f"\n🔧 CONVERSATION STATE MANAGER - Session {session_id}")
        logger.info(f"✅ Initialization complete for {current_section}")
        logger.info(f"📊 Total fields in section: {len(all_fields)}")
        logger.info(f"📋 Fields remaining to ask: {len(state.unasked_fields)}")
        logger.info(f"🎯 Unasked fields: {state.unasked_fields}")
        logger.info(f"{'='*50}")
        return state
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get session state (returns None if not initialized)"""
        return self.session_states.get(session_id)
    
    def mark_fields_asked(self, session_id: str, fields: List[str]):
        """Mark fields as asked for a session"""
        if session_id in self.session_states:
            state = self.session_states[session_id]
            logger.info(f"\n🎯 MARKING FIELDS AS ASKED - Session {session_id}")
            logger.info(f"📝 Fields being marked: {fields}")
            logger.info(f"📋 Before: {len(state.unasked_fields)} unasked fields")
            
            state.mark_fields_asked(fields)
            
            logger.info(f"📋 After: {len(state.unasked_fields)} unasked fields")
            logger.info(f"🔄 Remaining: {state.unasked_fields}")
            logger.info(f"{'='*30}")
        else:
            logger.warning(f"❌ Attempted to mark fields asked for uninitialized session: {session_id}")
    
    def is_section_complete(self, session_id: str) -> bool:
        """Check if current section is complete"""
        state = self.session_states.get(session_id)
        return state.is_section_complete() if state else False
    
    def move_to_next_section(self, session_id: str, next_section: str):
        """Move session to next section"""
        if session_id in self.session_states:
            self.session_states[session_id].reset_for_new_section(next_section)
        else:
            logger.warning(f"Attempted to move to next section for uninitialized session: {session_id}")
    
    def cleanup_old_sessions(self):
        """Remove sessions older than cleanup_interval"""
        cutoff_time = datetime.utcnow() - self.cleanup_interval
        expired_sessions = [
            session_id for session_id, state in self.session_states.items()
            if state.last_updated < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.session_states[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def _find_populated_fields(self, section_data: Dict[str, Any], all_fields: List[str]) -> List[str]:
        """Find which fields already have data in the section"""
        populated_fields = []
        
        for field_path in all_fields:
            if _field_has_data(section_data, field_path):
                populated_fields.append(field_path)
        
        return populated_fields
    
    def _map_verification_to_fields(self, verification_data: Dict[str, Any], section: str) -> List[str]:
        """Map verification/EHR data to field names for the current section"""
        mapped_fields = []
        
        if section == "intake_demographics":
            # Map EHR data to demographics fields
            ehr_to_field_map = {
                "first_name": "firstName",
                "last_name": "lastName", 
                "dob": "dateOfBirth",
                "gender": "gender",
                "email": "email",
                "mobile": "phone.mobile",
                "home_phone": "phone.home",
                "work_phone": "phone.work",
                "address_line1": "address.addressLine1",
                "address_line2": "address.addressLine2",
                "city": "address.city",
                "state": "address.state",
                "postal_code": "address.zipCode",
                "country": "address.country"
            }
            
            for ehr_field, intake_field in ehr_to_field_map.items():
                if verification_data.get(ehr_field):
                    mapped_fields.append(intake_field)
        
        # Add mappings for other sections as needed
        elif section == "intake_weight_history":
            # Map any relevant verification data for weight history
            pass
        elif section == "intake_medical_history":
            # Map any relevant verification data for medical history
            pass
        
        return mapped_fields
    
    def get_session_debug_info(self, session_id: str) -> Dict[str, Any]:
        """Get debug information about a session"""
        state = self.session_states.get(session_id)
        if not state:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "current_section": state.current_section,
            "initialized": state.initialized,
            "unasked_fields_count": len(state.unasked_fields),
            "unasked_fields": state.unasked_fields,
            "asked_this_turn": state.asked_this_turn,
            "is_section_complete": state.is_section_complete(),
            "last_updated": state.last_updated.isoformat()
        }


# Global instance
conversation_state_manager = ConversationStateManager()