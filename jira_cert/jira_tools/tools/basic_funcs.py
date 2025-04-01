import os
import requests
from requests.exceptions import HTTPError

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
    cert_path, key_path = setup_client_cert_files()

    try:
        response = requests.get(
            user_search_url, 
            cert=(cert_path, key_path),
            headers={"Accept": "application/json"},
            verify=False
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

def setup_client_cert_files():
    """
    Gets client certificate and key from environment variables and writes them to files.
    Returns tuple of (cert_path, key_path).
    """
    # Get certificate and key content from environment variables
    CLIENT_CERT = os.getenv("JIRA_CLIENT_CERT")
    CLIENT_KEY = os.getenv("JIRA_CLIENT_KEY")

    if not CLIENT_CERT or not CLIENT_KEY:
        raise ValueError("JIRA_CLIENT_CERT and JIRA_CLIENT_KEY environment variables must be set")

    # Create temporary paths for the cert files
    cert_path = "/tmp/jira_client.crt"
    key_path = "/tmp/jira_client.key"

    # Write the certificates to files
    with open(cert_path, 'w') as f:
        f.write(CLIENT_CERT)
    with open(key_path, 'w') as f:
        f.write(CLIENT_KEY)

    return cert_path, key_path 