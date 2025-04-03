import os
import logging
import requests
from requests.exceptions import HTTPError
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_jira_server_url() -> str:
    """Get the Jira server URL from environment"""
    server_url = os.getenv("JIRA_SERVER_URL")
    if not server_url:
        raise ValueError("JIRA_SERVER_URL environment variable must be set")
    url = server_url.rstrip('/')  # Remove trailing slash if present
    logger.info(f"Using Jira server URL: {url}")
    return url

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
        logger.error(f"Failed to get user ID: {e}")
        raise RuntimeError(f"Failed to get user ID: {e}")

def get_jira_auth() -> tuple:
    """Get Jira username and password from environment"""
    creds = os.getenv("JIRA_USER_CREDS")
    if not creds:
        raise ValueError("JIRA_USER_CREDS environment variable must be set (format: username:password)")
    try:
        username, password = creds.split(":")
        return (username, password)
    except ValueError:
        raise ValueError("JIRA_USER_CREDS must be in format 'username:password'")

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
    logger.info("Setting up client certificate files...")
    
    # Get certificate and key content from environment variables
    CLIENT_CERT = os.getenv("JIRA_CLIENT_CERT")
    CLIENT_KEY = os.getenv("JIRA_CLIENT_KEY")

    if not CLIENT_CERT or not CLIENT_KEY:
        raise ValueError("JIRA_CLIENT_CERT and JIRA_CLIENT_KEY environment variables must be set")

    # Log certificate details (safely)
    logger.info("Certificate validation:")
    logger.info(f"Certificate length: {len(CLIENT_CERT)} characters")
    logger.info(f"Private key length: {len(CLIENT_KEY)} characters")
    logger.info(f"Certificate starts with: {CLIENT_CERT[:25]}...")
    logger.info(f"Private key starts with: {CLIENT_KEY[:25]}...")

    # Create temporary paths for the cert files
    cert_path = "/tmp/jira_client.crt"
    key_path = "/tmp/jira_client.key"

    # Write the certificates to files
    try:
        # Ensure the certificate content is properly formatted
        if "BEGIN CERTIFICATE" not in CLIENT_CERT:
            logger.info("Adding certificate markers")
            CLIENT_CERT = f"-----BEGIN CERTIFICATE-----\n{CLIENT_CERT}\n-----END CERTIFICATE-----"
        if "BEGIN PRIVATE KEY" not in CLIENT_KEY:
            logger.info("Adding private key markers")
            CLIENT_KEY = f"-----BEGIN PRIVATE KEY-----\n{CLIENT_KEY}\n-----END PRIVATE KEY-----"

        logger.info(f"Writing certificate to: {cert_path}")
        with open(cert_path, 'w') as f:
            f.write(CLIENT_CERT)
        
        logger.info(f"Writing private key to: {key_path}")
        with open(key_path, 'w') as f:
            f.write(CLIENT_KEY)

        # Set proper permissions
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)

        # Verify files exist and have content
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            raise ValueError("Certificate files were not created properly")
        
        cert_size = os.path.getsize(cert_path)
        key_size = os.path.getsize(key_path)
        logger.info(f"Certificate file size: {cert_size} bytes")
        logger.info(f"Private key file size: {key_size} bytes")
        
        if cert_size == 0 or key_size == 0:
            raise ValueError("Certificate files are empty")

        # Read back files to verify content
        with open(cert_path, 'r') as f:
            cert_content = f.read()
            logger.info(f"Certificate file contains BEGIN/END markers: {('BEGIN CERTIFICATE' in cert_content)} / {('END CERTIFICATE' in cert_content)}")
        
        with open(key_path, 'r') as f:
            key_content = f.read()
            logger.info(f"Key file contains BEGIN/END markers: {('BEGIN PRIVATE KEY' in key_content)} / {('END PRIVATE KEY' in key_content)}")

        return cert_path, key_path

    except Exception as e:
        logger.error(f"Error setting up certificate files: {str(e)}")
        raise

def test_jira_connection():
    """Test the Jira connection with current credentials"""
    try:
        logger.info("\n=== Testing Jira Connection ===")
        server_url = get_jira_server_url()
        cert_path, key_path = setup_client_cert_files()
        
        # Try to access a simple endpoint
        test_url = f"{server_url}/rest/api/3/myself"
        logger.info(f"Testing connection to: {test_url}")
        
        headers = get_jira_basic_headers()
        logger.info(f"Request headers: {headers}")
        
        logger.info("Making test request...")
        response = requests.get(
            test_url,
            headers=headers,
            cert=(cert_path, key_path),
            verify=False
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            logger.error("Authentication failed (401)")
            logger.error(f"Response body: {response.text}")
            try:
                error_details = response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error("Could not parse error response as JSON")
        
        if response.status_code == 200:
            logger.info("Successfully connected to Jira!")
            logger.info(f"Response body: {response.text}")
            return True
        else:
            logger.error(f"Failed to connect. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        logger.error("SSL Error occurred:")
        logger.error(str(e))
        if "certificate verify failed" in str(e):
            logger.error("Certificate verification failed. This might indicate an issue with the certificate format or content.")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection Error occurred:")
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"Connection test failed with exception: {str(e)}")
        return False 