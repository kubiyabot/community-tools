import logging
import os
from typing import Dict, Any
from .tools import initialize_tools, tools
from .tools.config import DEFAULT_JENKINS_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JenkinsOpsError(Exception):
    """Base exception for Jenkins Operations module."""
    pass

def discover():
    """Entry point for tool discovery."""
    logger.info("Starting Jenkins Operations tool discovery...")
    
    try:
        def setup_default_environment():
            if not os.environ.get('JENKINS_URL'):
                os.environ['JENKINS_URL'] = DEFAULT_JENKINS_CONFIG['jenkins_url']
                logger.info(f"Using default Jenkins URL: {DEFAULT_JENKINS_CONFIG['jenkins_url']}")
            
            if not os.environ.get('JENKINS_API_TOKEN'):
                os.environ['JENKINS_API_TOKEN'] = "KYlJppNVnJQP5K1r"
                logger.info("Using default Jenkins API token")

        # Setup environment
        setup_default_environment()
        
        # Initialize tools
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
        raise JenkinsOpsError(error_msg)

# Export the tools
__all__ = ['tools', 'discover']

# Run discovery when the package is imported
if __name__ == "__main__":
    tools = discover()
    for tool in tools:
        print(tool)