"""
Repository layer for chat history operations with Supabase
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)


class ChatHistoryRepository:
    """Repository for managing chat history data in Supabase"""
    
    def __init__(self):
        self.table_name = "n8n_chat_histories"
    
    def _get_client(self):
        """Get Supabase client"""
        return get_supabase_client()
    
    async def add_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a single message to chat history
        
        Args:
            session_id: The session identifier
            message: Dictionary containing message data (role, content, timestamp, etc.)
        
        Returns:
            bool: True if successful, raises exception on failure
        """
        try:
            message_data = {
                "session_id": session_id,
                "message": message
            }
            
            response = self._get_client().table(self.table_name).insert(message_data).execute()
            
            if not response.data:
                raise Exception("Failed to add message")
            
            logger.debug(f"Added message to chat history for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to chat history for session {session_id}: {e}")
            raise
    
    async def add_messages(self, session_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Add multiple messages to chat history
        
        Args:
            session_id: The session identifier
            messages: List of message dictionaries
        
        Returns:
            bool: True if successful, raises exception on failure
        """
        try:
            message_data = [
                {
                    "session_id": session_id,
                    "message": message
                }
                for message in messages
            ]
            
            response = self._get_client().table(self.table_name).insert(message_data).execute()
            
            if not response.data:
                raise Exception("Failed to add messages")
            
            logger.debug(f"Added {len(messages)} messages to chat history for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding messages to chat history for session {session_id}: {e}")
            raise
    
    async def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: The session identifier
            limit: Optional limit on number of messages to retrieve (most recent first)
        
        Returns:
            List[Dict]: List of message dictionaries ordered by creation time
        """
        try:
            query = self._get_client().table(self.table_name).select("message").eq("session_id", session_id).order("id", desc=False)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            # Extract just the message content from each record
            messages = [record["message"] for record in response.data]
            
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history for session {session_id}: {e}")
            raise
    
    async def get_recent_messages(self, session_id: str, count: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent messages for a session (for maintaining context window)
        
        Args:
            session_id: The session identifier
            count: Number of recent messages to retrieve
        
        Returns:
            List[Dict]: List of recent message dictionaries
        """
        try:
            response = (
                self._get_client()
                .table(self.table_name)
                .select("message")
                .eq("session_id", session_id)
                .order("id", desc=True)
                .limit(count)
                .execute()
            )
            
            # Extract messages and reverse to get chronological order
            messages = [record["message"] for record in response.data]
            messages.reverse()  # Most recent last for conversation flow
            
            logger.debug(f"Retrieved {len(messages)} recent messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving recent messages for session {session_id}: {e}")
            raise
    
    async def clear_conversation_history(self, session_id: str) -> bool:
        """
        Clear all conversation history for a session
        
        Args:
            session_id: The session identifier
        
        Returns:
            bool: True if successful, raises exception on failure
        """
        try:
            response = self._get_client().table(self.table_name).delete().eq("session_id", session_id).execute()
            
            logger.info(f"Cleared conversation history for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation history for session {session_id}: {e}")
            raise
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a conversation
        
        Args:
            session_id: The session identifier
        
        Returns:
            Dict: Summary including message count, first/last message times, etc.
        """
        try:
            response = (
                self._get_client()
                .table(self.table_name)
                .select("id, message")
                .eq("session_id", session_id)
                .order("id", desc=False)
                .execute()
            )
            
            if not response.data:
                return {
                    "session_id": session_id,
                    "message_count": 0,
                    "conversation_started": None,
                    "last_message": None
                }
            
            messages = response.data
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "conversation_started": messages[0]["message"].get("timestamp"),
                "last_message": messages[-1]["message"].get("timestamp"),
                "first_message_id": messages[0]["id"],
                "last_message_id": messages[-1]["id"]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary for session {session_id}: {e}")
            raise


# Global repository instance
chat_history_repository = ChatHistoryRepository()