"""Jenkins Tools Package

This package provides tools for managing Jenkins operations.
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
    """Initialize Jenkins tools."""
    try:
        logger.info("Starting Jenkins tools initialization...")
        
        # Import tools after logging is configured
        from .tools.builds import BuildAnalyzer
        from .tools.config import ConfigAnalyzer
        
        # Create tool instances
        build_analyzer = BuildAnalyzer()
        config_analyzer = ConfigAnalyzer()
        
        # Register tools
        tool_registry.register("jenkins", build_analyzer)
        tool_registry.register("jenkins", config_analyzer)
        
        # Set version if available
        version = os.getenv('KUBIYA_VERSION', 'development')
        logger.info(f"Running version: {version}")
        
        logger.info("Jenkins tools initialization completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        raise

# Run initialization when module is imported
logger.info("Loading Jenkins tools module...")
initialize()

__version__ = "0.1.0"
