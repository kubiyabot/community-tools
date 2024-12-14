import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        tools = initialize_tools()
        logger.info(f"Successfully initialized {len(tools)} Terraform tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

# Initialize tools when module is imported
tools = initialize()

# Export the tools and initialization function
__all__ = ['tools', 'initialize']
