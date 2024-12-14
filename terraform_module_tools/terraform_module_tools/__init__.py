import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        initialized_tools = initialize_tools()
        if not initialized_tools:
            logger.warning("No tools were initialized")
            return []
            
        logger.info(f"Successfully initialized {len(initialized_tools)} Terraform tools")
        return initialized_tools
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

# Initialize tools when module is imported and store them
tools = initialize()

if not tools:
    logger.warning("No Terraform tools were initialized. Please check your configuration.")

# Export the tools and initialization function
__all__ = ['tools', 'initialize']
