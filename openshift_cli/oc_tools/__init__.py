# oc_tools/__init__.py
import os
import sys
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize OpenShift CLI tools."""
    try:
        logger.info("Starting OpenShift CLI tools initialization...")
        logger.info("OpenShift CLI tools initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenShift CLI tools: {str(e)}")
        raise

# Run initialization when module is imported
logger.info("Loading OpenShift CLI tools module...")
initialize()

# Import tools after initialization
from .tools import *
