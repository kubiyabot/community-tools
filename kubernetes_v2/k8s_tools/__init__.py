# k8s_tools/__init__.py
import os
import sys
import logging
import sentry_sdk
from .utils.sentry_client import initialize_sentry

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry immediately
logger.info("Initializing Sentry...")
if not initialize_sentry(force=True):
    logger.error("Failed to initialize Sentry")
else:
    logger.info("Sentry initialized successfully")

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        logger.info("Starting Kubernetes tools initialization...")
        
        # Ensure Sentry is working
        sentry_sdk.capture_message(
            "Starting Kubernetes tools initialization",
            level='info'
        )
        
        # Import initialization after Sentry is ready
        from .initialization import initialize as init_kubewatch
        
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

# Run initialization when module is imported
logger.info("Loading Kubernetes tools module...")
initialize()

# Import tools after initialization
from .tools import *