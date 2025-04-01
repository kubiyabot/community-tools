import os
import requests
from requests.exceptions import HTTPError

def get_cert_paths():
    """Get paths to the certificate and key files"""
    cert_path = "/tmp/jira_client.crt"
    key_path = "/tmp/jira_client.key"
    
    # Verify files exist
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        raise ValueError("Certificate or key file not found. Please ensure JIRA_CLIENT_CERT and JIRA_CLIENT_KEY are properly set.")
    
    return (cert_path, key_path)

def get_jira_server_url() -> str:
    """Get the Jira server URL from environment"""
    server_url = os.getenv("JIRA_SERVER_URL")
    if not server_url:
        raise ValueError("JIRA_SERVER_URL environment variable must be set")
    return server_url.rstrip('/')  # Remove trailing slash if present

def get_jira_user_id(email: str) -> str:
    """Get user account ID by email"""
    server_url = get_jira_server_url()
    user_search_url = f"{server_url}/rest/api/3/user/search?query={email}"
    cert_path, key_path = get_cert_paths()

    try:
        response = requests.get(
            user_search_url, 
            cert=(cert_path, key_path),
            headers={"Accept": "application/json"},
            verify=False  # Often needed for self-hosted instances with self-signed certs
        )
        response.raise_for_status()
        return response.json()[0]["accountId"]
    except HTTPError as e:
        print(f"Failed to get user ID: {e}")
        raise RuntimeError(f"Failed to get user ID: {e}")

def get_jira_basic_headers() -> dict:
    """Get basic headers for Jira API requests"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    } 