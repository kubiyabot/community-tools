import logging
from .tools import initialize_tools
from .parser import TerraformModuleParser, ModuleSource

logger = logging.getLogger(__name__)

def initialize_terraform_tools(config=None):
    """Initialize all Terraform tools with given configuration."""
    try:
        if config is None:
            config = {}
            
        # Initialize all tools (both module tools and terraformer if enabled)
        return initialize_tools(config)
    except Exception as e:
        logger.error(f"Failed to initialize Terraform tools: {str(e)}")
        raise

__all__ = ['initialize_terraform_tools', 'TerraformModuleParser', 'ModuleSource']
