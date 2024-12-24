import logging
from .tools import initialize_tools
from .parser import TerraformModuleParser, ModuleSource
from .scripts.config_loader import load_config, get_module_configs, ConfigurationError

logger = logging.getLogger(__name__)

def initialize_terraform_tools(config=None):
    """Initialize all Terraform tools with given configuration."""
    try:
        if config is None:
            config = {}
            
        # Load and validate configuration
        try:
            config = load_config()
            # Get module configurations
            module_configs = get_module_configs(config)
            
            # Initialize all tools with validated configurations
            return initialize_tools(config)
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e.get_formatted_message()}")
            raise
            
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

__all__ = ['initialize_terraform_tools', 'TerraformModuleParser', 'ModuleSource']
