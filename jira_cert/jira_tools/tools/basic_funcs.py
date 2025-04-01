import os
import logging
import requests
from requests.exceptions import HTTPError

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

def get_jira_basic_headers() -> dict:
    """Get basic headers for Jira API requests"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check"
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

    logger.debug(f"Certificate length: {len(CLIENT_CERT)} characters")
    logger.debug(f"Private key length: {len(CLIENT_KEY)} characters")

    # Create temporary paths for the cert files
    cert_path = "/tmp/jira_client.crt"
    key_path = "/tmp/jira_client.key"

    # Write the certificates to files
    try:
        # Ensure the certificate content is properly formatted
        if "BEGIN CERTIFICATE" not in CLIENT_CERT:
            logger.debug("Adding certificate markers to certificate content")
            CLIENT_CERT = f"-----BEGIN CERTIFICATE-----\n{CLIENT_CERT}\n-----END CERTIFICATE-----"
        if "BEGIN PRIVATE KEY" not in CLIENT_KEY:
            logger.debug("Adding private key markers to key content")
            CLIENT_KEY = f"-----BEGIN PRIVATE KEY-----\n{CLIENT_KEY}\n-----END PRIVATE KEY-----"

        logger.debug(f"Writing certificate to: {cert_path}")
        with open(cert_path, 'w') as f:
            f.write(CLIENT_CERT)
        
        logger.debug(f"Writing private key to: {key_path}")
        with open(key_path, 'w') as f:
            f.write(CLIENT_KEY)

        # Set proper permissions
        logger.debug("Setting file permissions...")
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)

        # Verify files exist and have content
        cert_size = os.path.getsize(cert_path)
        key_size = os.path.getsize(key_path)
        logger.debug(f"Certificate file size: {cert_size} bytes")
        logger.debug(f"Private key file size: {key_size} bytes")
        
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            raise ValueError("Certificate files were not created properly")
        if cert_size == 0 or key_size == 0:
            raise ValueError("Certificate files are empty")

        return cert_path, key_path

    except Exception as e:
        logger.error(f"Error setting up certificate files: {str(e)}")
        raise

def test_jira_connection():
    """Test the Jira connection with current credentials"""
    try:
        logger.info("=== Testing Jira Connection ===")
        server_url = get_jira_server_url()
        cert_path, key_path = setup_client_cert_files()
        
        # Try to access a simple endpoint
        test_url = f"{server_url}/rest/api/3/myself"
        logger.info(f"Testing connection to: {test_url}")
        
        headers = get_jira_basic_headers()
        logger.debug(f"Using headers: {headers}")
        
        logger.info("Making test request...")
        response = requests.get(
            test_url,
            headers=headers,
            cert=(cert_path, key_path),
            verify=False
        )
        
        logger.info(f"Connection test status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("Successfully connected to Jira!")
            logger.debug(f"Response body: {response.text}")
            return True
        else:
            logger.error(f"Failed to connect. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Connection test failed with exception: {str(e)}")
        if isinstance(e, requests.exceptions.SSLError):
            logger.error("SSL Error - This might indicate a certificate problem")
        elif isinstance(e, requests.exceptions.ConnectionError):
            logger.error("Connection Error - This might indicate a network or URL problem")
        return False 