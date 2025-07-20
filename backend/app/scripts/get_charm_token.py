#!/usr/bin/env python3
"""
Script to obtain and update Charm Tracker OAuth tokens.

This script guides the user through the OAuth flow to get a new access token
and refresh token from Charm Tracker, then updates the authTokens table.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_supabase_client
from app.core.config import get_settings

# Load environment variables
load_dotenv()

# OAuth URL for user authorization
OAUTH_URL = """https://accounts.charmtracker.com/oauth/v2/auth?scope=charmhealth.user.setting.facility.READ,charmhealth.user.setting.member.READ,charmhealth.patient.demographics.ALL,charmhealth.user.calendar.ALL,charmhealth.patient.questionnaire.ALL,charmhealth.patient.insurance.ALL,charmhealth.patient.document.ALL,charmhealth.user.task.ALL,charmhealth.user.message.ALL,charmhealth.patient.problem.ALL,charmhealth.user.setting.ALL,charmhealth.patient.careteam.ALL,charmhealth.user.template.ALL,charmhealth.patient.chartnote.ALL,charmhealth.patient.vital.ALL,charmhealth.user.setting.questionnaire.ALL,charmhealth.patient.invoice.CREATE,charmhealth.patient.invoice.READ,charmhealth.patient.receipt.READ,charmhealth.user.setting.billing.READ,charmhealth.patient.medication.ALL,charmhealth.patient.medicalhistory.ALL,charmhealth.patient.allergy.all,charmhealth.patient.cardonfile.ALL&client_id=1000.K4N20ZUE3B73CBRAGRX3FDQTHIN06J&state=test&response_type=code&redirect_uri=https://ehr2.charmtracker.com/ehr/physician/mySpace.do?ACTION=SHOW_OAUTH_JSON&access_type=offline&prompt=consent"""

def get_tokens_from_auth_code(access_code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    settings = get_settings()
    
    # Get credentials from environment
    client_id = os.getenv('CHARM_CLIENT_ID')
    client_secret = os.getenv('CHARM_CLIENT_SECRET')
    charm_api_key = os.getenv('CHARM_API_KEY')
    
    if not all([client_id, client_secret, charm_api_key]):
        raise ValueError("Missing required environment variables: CHARM_CLIENT_ID, CHARM_CLIENT_SECRET, or CHARM_API_KEY")
    
    # Construct token exchange URL
    token_url = f"https://accounts.charmtracker.com/oauth/v2/token?code={access_code}&client_id={client_id}&client_secret={client_secret}&redirect_uri=https://ehr2.charmtracker.com/ehr/physician/mySpace.do?ACTION=SHOW_OAUTH_JSON&grant_type=authorization_code"
    
    # Make POST request to get tokens
    headers = {"api_key": charm_api_key}
    response = requests.post(token_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get tokens: {response.status_code} - {response.text}")
    
    return response.json()

def update_auth_tokens(access_token: str, refresh_token: str):
    """Update the authTokens table with new tokens."""
    supabase = get_supabase_client()
    
    # Calculate token expiration (typically 1 hour for access tokens)
    expiration = datetime.utcnow() + timedelta(hours=1)
    expiration_str = expiration.isoformat()
    
    # Update the authTokens table (only stores access token and expiration)
    result = supabase.table('authTokens').update({
        'authToken': access_token,
        'tokenExpiration': expiration_str
    }).eq('tokenName', 'charm').execute()
    
    if not result.data:
        # If no existing record, insert a new one
        result = supabase.table('authTokens').insert({
            'tokenName': 'charm',
            'authToken': access_token,
            'tokenExpiration': expiration_str
        }).execute()
    
    return result

def main():
    print("=== Charm Tracker OAuth Token Update Script ===\n")
    
    # Step 1: Direct user to authorization URL
    print("Step 1: Authorization")
    print("-" * 50)
    print("Please click on the following link to authorize the application:")
    print(f"\n{OAUTH_URL}\n")
    print("After authorization, you will be redirected to a page showing JSON data.")
    print("Look for the 'code' parameter in the URL or in the JSON response.")
    
    # Step 2: Get the authorization code from user
    access_code = input("\nEnter the authorization code: ").strip()
    
    if not access_code:
        print("Error: No authorization code provided.")
        return
    
    print("\nStep 2: Exchanging authorization code for tokens...")
    print("-" * 50)
    
    try:
        # Get tokens from Charm Tracker
        token_response = get_tokens_from_auth_code(access_code)
        
        new_access_token = token_response.get('access_token')
        new_refresh_token = token_response.get('refresh_token')
        
        if not new_access_token or not new_refresh_token:
            print("Error: Invalid token response")
            print(f"Response: {token_response}")
            return
        
        print("✓ Successfully obtained tokens from Charm Tracker")
        
        # Step 3: Compare refresh tokens
        print("\nStep 3: Comparing refresh tokens...")
        print("-" * 50)
        
        current_refresh_token = os.getenv('CHARM_REFRESH_TOKEN')
        
        if current_refresh_token and current_refresh_token != new_refresh_token:
            print("\n⚠️  WARNING: Refresh token has changed!")
            print("Please update the following:")
            print("1. Update CHARM_REFRESH_TOKEN in your .env file")
            print("2. Update the refresh token in your secret manager")
            print(f"\nNew refresh token: {new_refresh_token}")
        else:
            print("✓ Refresh token is unchanged")
        
        # Step 4: Update database
        print("\nStep 4: Updating authTokens table...")
        print("-" * 50)
        
        result = update_auth_tokens(new_access_token, new_refresh_token)
        
        if result.data:
            print("✓ Successfully updated authTokens table")
            print(f"  - Token Name: charm")
            print(f"  - Access Token: {new_access_token[:20]}...")
            print("\nNote: The refresh token is stored in environment variables/secret manager,")
            print("      not in the database.")
        else:
            print("Error updating database:", result)
        
        print("\n✅ Token update process completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()