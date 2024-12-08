import logging
import os
from typing import Dict, Any

from jenkins_ops.tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default Jenkins settings for in-cluster access
DEFAULT_JENKINS_CONFIG: Dict[str, Any] = {
    "jenkins_url": "http://jenkins.jenkins.svc.cluster.local:8080",
    "auth": {
        "username": "admin",
        "password_env": "JENKINS_API_TOKEN"
    },
    "jobs": {
        "sync_all": True  # By default, sync all jobs
    },
    "defaults": {
        "stream_logs": True,
        "poll_interval": 30,
        "long_running_threshold": 300
    }
}

def setup_default_environment():
    """Setup default environment variables if not present."""
    if not os.environ.get('JENKINS_URL'):
        os.environ['JENKINS_URL'] = DEFAULT_JENKINS_CONFIG['jenkins_url']
    
    if not os.environ.get('JENKINS_API_TOKEN'):
        os.environ['JENKINS_API_TOKEN'] = "KYlJppNVnJQP5K1r"

def initialize_module():
    """Initialize the module with default or configured settings."""
    try:
        # Setup default environment
        setup_default_environment()
        
        # Initialize tools
        discovered_tools = initialize_tools()
        
        if not discovered_tools:
            logger.warning("No Jenkins tools were discovered. Check Jenkins connection and configuration.")
        else:
            logger.info(f"Successfully discovered {len(discovered_tools)} Jenkins tools")
        
        return discovered_tools
    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        return []

# Initialize tools when module is imported
tools = initialize_module()

# Export the tools and initialization functions
__all__ = ['tools', 'initialize_module', 'DEFAULT_JENKINS_CONFIG'] 