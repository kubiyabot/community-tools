import logging
from .tools.dynamic_tool_loader import load_terraform_tools
from kubiya_sdk.tools.registry import tool_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        
        # Load tools using dynamic configuration
        initialized_tools = load_terraform_tools()
        
        if initialized_tools:
            logger.info(f"Successfully initialized {len(initialized_tools)} Terraform tools")
            return initialized_tools
        else:
            logger.warning("No tools were initialized")
            return []
            
    except Exception as e:
        error_msg = f"Failed to initialize Terraform tools: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Export the initialization function
__all__ = ['initialize']
