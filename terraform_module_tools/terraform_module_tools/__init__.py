import logging
import os
from pathlib import Path
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_terraform_modules():
    """Initialize and load all Terraform module tools."""
    try:
        logger.info("🔍 Scanning for Terraform module configurations...")
        
        # Get configs directory - FIXED PATH
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')
        logger.info(f"Looking for configs in: {config_dir}")
        
        if not os.path.exists(config_dir):
            # Try alternate location
            alt_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs')
            logger.info(f"Config dir not found, trying alternate location: {alt_config_dir}")
            if os.path.exists(alt_config_dir):
                config_dir = alt_config_dir
            else:
                raise FileNotFoundError(f"Configuration directory not found in either {config_dir} or {alt_config_dir}")
        
        # Find all JSON config files
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        if not config_files:
            logger.warning("⚠️ No module configurations found!")
            return []
            
        logger.info(f"📋 Found {len(config_files)} module configurations: {', '.join(config_files)}")
        
        # Initialize tools
        tools = initialize_tools(config_dir)  # Pass config_dir to initialize_tools
        
        if tools:
            logger.info(f"✅ Successfully loaded {len(tools)} Terraform tools")
            for tool in tools:
                logger.info(f"  - {tool.name}")
        else:
            logger.warning("⚠️ No tools were created from configurations")
            
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to load Terraform modules: {str(e)}", exc_info=True)
        raise

# Load tools when package is imported
try:
    tools = load_terraform_modules()
except Exception as e:
    logger.error(f"Failed to load tools: {str(e)}", exc_info=True)
    tools = []

# Export functions and tools
__all__ = ['tools', 'load_terraform_modules']
