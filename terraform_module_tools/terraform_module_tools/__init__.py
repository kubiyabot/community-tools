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
        
        # Get configs directory
        config_dir = os.path.join(os.path.dirname(__file__), 'configs')
        if not os.path.exists(config_dir):
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
        
        # Find all JSON config files
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        if not config_files:
            logger.warning("⚠️ No module configurations found!")
            return []
            
        logger.info(f"📋 Found {len(config_files)} module configurations")
        
        # Initialize tools
        tools = initialize_tools()
        
        if tools:
            logger.info(f"✅ Successfully loaded {len(tools)} Terraform tools")
            for tool in tools:
                logger.info(f"  - {tool.name}")
        else:
            logger.warning("⚠️ No tools were created from configurations")
            
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to load Terraform modules: {str(e)}")
        raise

# Load tools when package is imported
tools = load_terraform_modules()

# Export functions and tools
__all__ = ['tools', 'load_terraform_modules']
