import logging
from terraform_module_tools.tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Terraform module tools."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        tools = initialize_tools()
        if tools:
            logger.info(f"Successfully initialized {len(tools)} Terraform tools")
            return tools
        else:
            logger.warning("No tools were initialized")
            return []
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

# Initialize and export tools when package is imported
tools = initialize()

# Export the tools and initialization function
__all__ = ['tools', 'initialize']
