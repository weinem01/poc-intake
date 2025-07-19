"""
Pydantic AI-based intake agent for intelligent conversation management
Replaces LangChain with type-safe, structured data collection
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from app.core.config import get_settings
from app.models.intake_schemas import IntakeSession
from app.repositories.intake_repository import intake_repository

logger = logging.getLogger(__name__)


class IdentityExtraction(BaseModel):
    """Model for extracting identity information from user input"""
    last_name: str = Field(description="Patient's last name extracted from the message")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD format")
    confidence: float = Field(description="Confidence score between 0 and 1")
    original_date_format: str = Field(description="The original date format found in the message")


class DemographicsUpdate(BaseModel):
    """Model for updating demographics information"""
    field_name: str = Field(description="The field being updated (e.g., 'email', 'phone.mobile')")
    new_value: str = Field(description="The new value for the field")
    confidence: float = Field(description="Confidence in the extraction")


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


class PydanticIntakeAgent:
    """
    Pydantic AI agent for managing patient intake conversations
    Provides type-safe, structured data collection with intelligent conversation flow
    """
    
    def __init__(self):
        settings = get_settings()
        self.model = OpenAIModel('gpt-4', api_key=settings.get_openai_api_key())
        
        # Identity extraction agent
        self.identity_agent = Agent(
            self.model,
            result_type=IdentityExtraction,
            system_prompt="""
            You are a medical intake assistant specializing in identity verification.
            Extract the patient's last name and date of birth from their message.
            
            Look for:
            - Last name (surname/family name)
            - Date of birth in any format (MM/DD/YYYY, M/D/YY, MM-DD-YYYY, etc.)
            
            Convert dates to YYYY-MM-DD format while preserving the original format.
            Provide high confidence (0.8+) only when both pieces are clearly present.
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
        
        # Main conversation agent
        self.conversation_agent = Agent(
            self.model,
            result_type=IntakeAgentResponse,
            system_prompt="""
            You are a friendly, professional medical intake assistant for Pound of Cure Weight Loss clinic.
            
            Your role is to:
            1. Guide patients through their intake form completion
            2. Ask relevant follow-up questions for missing information
            3. Confirm and validate information provided
            4. Maintain a conversational, empathetic tone
            
            Current intake sections:
            - intake_demographics: Basic patient information
            - intake_insurance: Insurance and billing information  
            - intake_weight_history: Weight and diet history
            - intake_medical_history: Medical conditions, medications, allergies
            
            Guidelines:
            - Ask one question at a time
            - Be specific about what information you need
            - Confirm information before moving to the next section
            - Use natural, conversational language
            - Show empathy for sensitive topics (weight, medical conditions)
            """
        )
    
    async def extract_identity(self, message: str) -> IdentityExtraction:
        """Extract identity information from user message"""
        try:
            result = await self.identity_agent.run(message)
            return result.data
        except Exception as e:
            logger.error(f"Error extracting identity: {e}")
            return IdentityExtraction(
                last_name="",
                date_of_birth="",
                confidence=0.0,
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
                new_value="",
                confidence=0.0
            )
    
    async def process_conversation(self, message: str, context: IntakeContext) -> IntakeAgentResponse:
        """Process the main intake conversation"""
        try:
            # Build conversation prompt with context
            prompt = f"""
            Session ID: {context.session_id}
            Current Section: {context.current_section}
            
            Patient Data Available: {bool(context.patient_data)}
            Current Intake Data: {context.intake_data}
            
            Conversation History:
            {self._format_conversation_history(context.conversation_history)}
            
            User Message: {message}
            
            Based on the current section and available data, provide an appropriate response to guide the patient through their intake process.
            """
            
            result = await self.conversation_agent.run(prompt)
            return result.data
            
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
    
    async def determine_next_section(self, current_data: Dict[str, Any]) -> str:
        """Determine the next section based on current intake data completion"""
        return intake_repository.determine_current_section(current_data)


# Global agent instance
pydantic_intake_agent = PydanticIntakeAgent()