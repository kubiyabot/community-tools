"""ArgoCD Tools Package

This package provides tools for managing ArgoCD operations.
"""
import os
import sys
import logging
from kubiya_sdk.tools.registry import tool_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize ArgoCD tools."""
    try:
        logger.info("Starting ArgoCD tools initialization...")
        
        # Import tools after logging is configured
        from .tools.core import CoreOperations
        from .tools.applications import ApplicationManager
        
        # Initialize core operations
        CoreOperations()
        
        # Set version if available
        version = os.getenv('KUBIYA_VERSION', 'development')
        logger.info(f"Running version: {version}")
        
        logger.info("ArgoCD tools initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize ArgoCD tools: {str(e)}")
        raise

# Run initialization when module is imported
logger.info("Loading ArgoCD tools module...")
initialize()

__version__ = "0.1.0"
