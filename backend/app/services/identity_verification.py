"""
Patient identity verification service
Handles confirmation of patient last name and date of birth
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class IdentityVerificationService:
    """Service for verifying patient identity"""
    
    def __init__(self):
        pass
    
    def extract_name_from_message(self, message: str) -> Optional[str]:
        """
        Extract a last name from a user message
        Looks for common patterns like "my last name is...", "Smith", etc.
        """
        # Clean the message
        message = message.strip().lower()
        
        # Common patterns for last name responses
        patterns = [
            r"my last name is\s+([a-zA-Z\-\']+)",
            r"last name is\s+([a-zA-Z\-\']+)",
            r"surname is\s+([a-zA-Z\-\']+)",
            r"family name is\s+([a-zA-Z\-\']+)",
            r"^([a-zA-Z\-\']+)$",  # Just the name alone
            r"it\'s\s+([a-zA-Z\-\']+)",
            r"name:\s*([a-zA-Z\-\']+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                # Validate it looks like a name (2+ characters, no numbers)
                if len(name) >= 2 and name.isalpha():
                    return name.title()  # Capitalize properly
        
        return None
    
    def extract_date_from_message(self, message: str) -> Optional[str]:
        """
        Extract a date of birth from a user message
        Supports various formats: MM/DD/YYYY, MM-DD-YYYY, Month DD, YYYY, etc.
        """
        # Clean the message
        message = message.strip()
        
        # Date patterns to match
        patterns = [
            # MM/DD/YYYY or MM/DD/YY
            r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4}|\d{2})",
            # Month DD, YYYY
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})",
            # DD Month YYYY
            r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
            # YYYY-MM-DD
            r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})"
        ]
        
        message_lower = message.lower()
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, message_lower)
            if match:
                try:
                    if i == 0:  # MM/DD/YYYY or MM/DD/YY
                        month, day, year = match.groups()
                        if len(year) == 2:
                            year = "19" + year if int(year) > 30 else "20" + year
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif i == 1:  # Month DD, YYYY
                        month_name, day, year = match.groups()
                        month_num = self._month_name_to_number(month_name)
                        date_str = f"{year}-{month_num:02d}-{day.zfill(2)}"
                    elif i == 2:  # DD Month YYYY
                        day, month_name, year = match.groups()
                        month_num = self._month_name_to_number(month_name)
                        date_str = f"{year}-{month_num:02d}-{day.zfill(2)}"
                    elif i == 3:  # YYYY-MM-DD
                        year, month, day = match.groups()
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    # Validate the date
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Sanity check: should be a reasonable birth date
                    current_year = datetime.now().year
                    birth_year = parsed_date.year
                    
                    if 1900 <= birth_year <= current_year - 1:  # At least 1 year old
                        return date_str
                        
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _month_name_to_number(self, month_name: str) -> int:
        """Convert month name to number"""
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        return months.get(month_name.lower(), 1)
    
    def verify_identity(
        self, 
        provided_last_name: str, 
        provided_dob: str, 
        patient_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify provided identity information against patient data
        Returns (is_verified, message)
        """
        if not patient_data:
            return False, "Unable to verify identity: patient data not available"
        
        # Check last name
        patient_last_name = patient_data.get("last_name", "").lower().strip()
        provided_last_name_clean = provided_last_name.lower().strip()
        
        if not patient_last_name or not provided_last_name_clean:
            return False, "Unable to verify identity: missing name information"
        
        # Allow for slight variations in name (e.g., hyphenated names, apostrophes)
        name_match = (
            provided_last_name_clean == patient_last_name or
            provided_last_name_clean in patient_last_name or
            patient_last_name in provided_last_name_clean
        )
        
        if not name_match:
            return False, "The last name provided does not match our records"
        
        # Check date of birth
        patient_dob = patient_data.get("date_of_birth", "")
        if not patient_dob:
            return False, "Unable to verify identity: missing date of birth in records"
        
        # Normalize date formats for comparison
        try:
            # Parse patient DOB (might be in different format)
            if isinstance(patient_dob, str):
                # Try common formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                    try:
                        patient_date = datetime.strptime(patient_dob, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False, "Unable to verify identity: invalid date format in records"
            else:
                patient_date = patient_dob  # Assume it's already a datetime
            
            provided_date = datetime.strptime(provided_dob, "%Y-%m-%d")
            
            if patient_date.date() != provided_date.date():
                return False, "The date of birth provided does not match our records"
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Date parsing error in identity verification: {e}")
            return False, "Unable to verify identity: date format error"
        
        return True, "Identity verified successfully"
    
    def generate_identity_prompt(
        self, 
        patient_data: Optional[Dict[str, Any]] = None,
        attempt_count: int = 1
    ) -> str:
        """
        Generate appropriate prompt for identity verification
        """
        if attempt_count == 1:
            if patient_data and patient_data.get("first_name"):
                return f"Hi {patient_data['first_name']}! To confirm your identity before we begin, could you please tell me your last name and date of birth?"
            else:
                return "To confirm your identity before we begin, could you please tell me your last name and date of birth?"
        
        elif attempt_count == 2:
            return "I need to verify both your last name and date of birth. Could you please provide both pieces of information? For example, you could say 'My last name is Smith and my date of birth is January 15, 1985'."
        
        elif attempt_count == 3:
            return "I'm having trouble verifying your identity. Please provide your last name and date of birth clearly. For the date, you can use formats like MM/DD/YYYY or spell out the month. If you continue to have issues, please contact our office directly."
        
        else:
            return "I apologize, but I'm unable to verify your identity after multiple attempts. For your security, please contact our office directly at your convenience to complete your intake."


# Global service instance
identity_service = IdentityVerificationService()