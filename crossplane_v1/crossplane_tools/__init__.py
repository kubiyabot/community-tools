"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
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
    """Initialize Crossplane tools."""
    try:
        logger.info("Starting Crossplane tools initialization...")
        
        # Import tools after logging is configured
        from .tools.core import (
            install_crossplane_tool,
            uninstall_crossplane_tool,
            get_status_tool,
            version_tool,
            debug_mode_tool
        )
        
        from .tools.providers import (
            install_provider_tool,
            configure_provider_tool,
            list_providers_tool,
            get_provider_status_tool,
            uninstall_provider_tool,
            apply_provider_resource_tool
        )
        
        # Set version if available
        version = os.getenv('KUBIYA_VERSION', 'development')
        logger.info(f"Running version: {version}")
        
        logger.info("Crossplane tools initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize Crossplane tools: {str(e)}")
        raise

# Run initialization when module is imported
logger.info("Loading Crossplane tools module...")
initialize()

__version__ = "0.1.0" 