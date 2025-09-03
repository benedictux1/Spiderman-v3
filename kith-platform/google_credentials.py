"""
Google Cloud Credentials Handler for Kith Platform
Handles Google Service Account authentication from environment variables
"""
import os
import json
import tempfile
from google.oauth2 import service_account

def get_google_credentials():
    """
    Get Google Cloud credentials from environment variable
    Returns the path to a temporary credentials file
    """
    # Check if credentials are provided as environment variable
    google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if not google_credentials_json:
        # Fallback to file path if JSON not provided
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            return credentials_path
        return None
    
    try:
        # Parse the JSON credentials
        credentials_dict = json.loads(google_credentials_json)
        
        # Create a temporary file with the credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(credentials_dict, f)
            temp_path = f.name
        
        # Set the environment variable for Google libraries
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
        
        return temp_path
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Google credentials JSON: {e}")
        return None
    except Exception as e:
        print(f"Error setting up Google credentials: {e}")
        return None

def setup_google_credentials():
    """Setup Google credentials for the application"""
    credentials_path = get_google_credentials()
    if credentials_path:
        print("Google Cloud credentials configured successfully")
        return True
    else:
        print("Warning: Google Cloud credentials not found")
        return False
