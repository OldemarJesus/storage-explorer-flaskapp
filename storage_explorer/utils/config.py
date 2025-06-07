import os, json

def get_api_key()-> dict:
    """Retrieve the API key from environment variables."""
    api_key_str = os.environ.get("API_KEY")
    if not api_key_str:
        raise ValueError("Google Cloud API key not found in environment variables.")
    
    try:
        api_key = json.loads(api_key_str)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format for Google Cloud API key.") from e
    
    return api_key