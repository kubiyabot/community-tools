import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize(dynamic_config=None):
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        if not dynamic_config:
            logger.warning("No dynamic configuration provided")
            return []

        # Convert dynamic config to module configurations
        module_configs = {}
        for module_name, config in dynamic_config.items():
            if isinstance(config, dict):
                module_configs[module_name] = {
                    'name': module_name,
                    'source': config['source'],
                    'version': config.get('version'),
                    'auto_discover': config.get('auto_discover', True),
                    'instructions': config.get('instructions'),
                    'variables': config.get('variables', {})
                }

        # Initialize tools with module configurations
        initialized_tools = initialize_tools(module_configs)
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
