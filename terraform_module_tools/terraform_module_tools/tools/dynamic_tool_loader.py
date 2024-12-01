import os
import json
from typing import Dict, Any, List
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from ..parser import TerraformModuleParser
from . import create_terraform_module_tool
import logging

logger = logging.getLogger(__name__)

def get_config_dir() -> str:
    """Get the path to the configs directory."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs')

def load_terraform_tools(config_dir: str = None):
    """Load and register all Terraform tools from configuration files."""
    tools = []
    
    if not config_dir:
        config_dir = get_config_dir()
        
    logger.info(f"Loading tools from config directory: {config_dir}")
    
    if not os.path.exists(config_dir):
        logger.error(f"Config directory not found: {config_dir}")
        return tools
    
    for filename in os.listdir(config_dir):
        if filename.endswith('.json'):
            config_path = os.path.join(config_dir, filename)
            try:
                logger.info(f"Processing config file: {filename}")
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                
                # Iterate through each module in the config file
                for module_id, config in configs.items():
                    try:
                        logger.info(f"📦 Loading module: {config['name']}")
                        
                        # Create tools for this module
                        for action in ['plan', 'apply']:
                            tool = create_terraform_module_tool(config, action)
                            tools.append(tool)
                            tool_registry.register("terraform", tool)
                            logger.info(f"✅ Created {action} tool for {config['name']}")
                            
                    except Exception as e:
                        logger.error(f"❌ Failed to create tools for module {module_id}: {str(e)}", exc_info=True)
                        continue
                
            except Exception as e:
                logger.error(f"❌ Failed to load config file {filename}: {str(e)}", exc_info=True)
                continue

    return tools

# Export the loader function
__all__ = ['load_terraform_tools']