import logging
import os
from typing import Dict, Any

from jenkins_ops.tools import initialize_tools
from jenkins_ops.config import DEFAULT_JENKINS_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JenkinsOpsError(Exception):
    """Base exception for Jenkins Operations module."""
    pass

def setup_default_environment():
    """Setup default environment variables if not present."""
    try:
        if not os.environ.get('JENKINS_URL'):
            os.environ['JENKINS_URL'] = DEFAULT_JENKINS_CONFIG['jenkins_url']
            logger.info(f"Using default Jenkins URL: {DEFAULT_JENKINS_CONFIG['jenkins_url']}")
        
        if not os.environ.get('JENKINS_API_TOKEN'):
            os.environ['JENKINS_API_TOKEN'] = "KYlJppNVnJQP5K1r"
            logger.info("Using default Jenkins API token")
    except Exception as e:
        raise JenkinsOpsError(f"Failed to setup environment: {str(e)}")

def initialize_module():
    """Initialize the module with default or configured settings."""
    try:
        # Setup default environment
        setup_default_environment()
        
        # Initialize tools
        logger.info("Starting Jenkins tools discovery...")
        discovered_tools = initialize_tools()
        
        if not discovered_tools:
            error_msg = "No Jenkins tools were discovered. Check Jenkins connection and configuration."
            logger.error(error_msg)
            raise JenkinsOpsError(error_msg)
        
        logger.info(f"Successfully discovered {len(discovered_tools)} Jenkins tools")
        return discovered_tools
        
    except Exception as e:
        error_msg = f"Failed to initialize Jenkins tools: {str(e)}"
        logger.error(error_msg)
        raise JenkinsOpsError(error_msg) from e

try:
    # Initialize tools when module is imported
    tools = initialize_module()
except Exception as e:
    logger.critical(f"Critical error during module initialization: {str(e)}")
    raise  # Re-raise the exception to prevent silent failures

# Export the tools and initialization functions
__all__ = ['tools', 'initialize_module', 'DEFAULT_JENKINS_CONFIG', 'JenkinsOpsError'] 