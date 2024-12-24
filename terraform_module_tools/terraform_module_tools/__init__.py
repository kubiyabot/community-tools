import logging
from .tools import initialize_tools
from .parser import TerraformModuleParser, ModuleSource
from .scripts.config_loader import load_config, ConfigurationError

logger = logging.getLogger(__name__)

def initialize_terraform_tools(input_config=None):
    """Initialize all Terraform tools with given configuration."""
    try:
        # Normalize input configuration
        if input_config is None:
            input_config = {}
            
        # If config is not under 'terraform' key, wrap it
        if 'terraform' not in input_config and any(
            key in input_config for key in [
                'enable_reverse_terraform',
                'reverse_terraform_providers',
                'modules',
                'tf_modules'
            ]
        ):
            input_config = {'terraform': input_config}
            
        # Load and validate configuration
        try:
            # Load and validate configuration
            config = load_config(input_config=input_config)
            logger.info(f"Loaded configuration: {config}")
            
            # Initialize all tools with validated configurations
            return initialize_tools(config)
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e.get_formatted_message()}")
            raise
            
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

__all__ = ['initialize_terraform_tools', 'TerraformModuleParser', 'ModuleSource']
