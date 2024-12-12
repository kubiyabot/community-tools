# k8s_tools/__init__.py
import os
import sys
import logging
import sentry_sdk
from .utils.sentry_client import initialize_sentry
from .initialization import initialize as init_kubewatch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        logger.info("Starting Kubernetes tools initialization...")
        
        # Ensure Sentry is initialized
        initialize_sentry()
        
        sentry_sdk.add_breadcrumb(
            category='initialization',
            message='Starting Kubernetes tools initialization',
            level='info'
        )
        
        # Set release version if available
        version = os.getenv('KUBIYA_VERSION', 'development')
        sentry_sdk.set_tag('release', version)
        
        init_kubewatch()
        
        sentry_sdk.capture_message(
            "Kubernetes tools initialization completed successfully",
            level='info'
        )
        logger.info("Kubernetes tools initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes tools: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise

# Initialize Sentry immediately when module is imported
initialize_sentry()

# Run initialization when module is imported
logger.info("Loading Kubernetes tools module...")
initialize()

from .tools import *