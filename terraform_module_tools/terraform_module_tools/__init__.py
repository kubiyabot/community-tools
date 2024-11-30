import logging
import os
from pathlib import Path
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_config_dir() -> str:
    """Get the path to the configs directory."""
    return os.path.join(os.path.dirname(__file__), 'configs')

def load_terraform_modules():
    """Initialize and load all Terraform module tools."""
    try:
        logger.info("🔍 Scanning for Terraform module configurations...")
        
        # Get configs directory - now inside the package
        config_dir = get_config_dir()
        logger.info(f"Looking for configs in: {config_dir}")
        
        if not os.path.exists(config_dir):
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
        
        # Find all JSON config files
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        if not config_files:
            logger.warning("⚠️ No module configurations found!")
            raise Exception("No module configurations found!")
            
        logger.info(f"📋 Found {len(config_files)} module configurations: {', '.join(config_files)}")
        
        # Initialize tools
        tools = initialize_tools(config_dir)
        
        if tools:
            logger.info(f"✅ Successfully loaded {len(tools)} Terraform tools")
            for tool in tools:
                logger.info(f"  - {tool.name}")
        else:
            logger.warning("⚠️ No tools were created from configurations")
            raise Exception("No tools were created from configurations")
            
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to load Terraform modules: {str(e)}", exc_info=True)
        raise e

# Load tools when package is imported
try:
    tools = load_terraform_modules()
except Exception as e:
    logger.error(f"Failed to load tools: {str(e)}", exc_info=True)
    tools = []
    raise e

# Export functions and tools
__all__ = ['tools', 'load_terraform_modules']
