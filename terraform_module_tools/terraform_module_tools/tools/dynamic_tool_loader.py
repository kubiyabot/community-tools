import os
import json
from typing import Dict, Any, List
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from ..parser import TerraformModuleParser, TerraformVariable
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
                    config = json.load(f)
                
                module_name = config.get('name')
                if not module_name:
                    logger.error(f"No module name found in {filename}")
                    continue
                    
                logger.info(f"📦 Loading module: {module_name}")
                
                # Parse module variables
                parser = TerraformModuleParser(
                    source_url=config['source']['location'],
                    ref=config['source'].get('git_config', {}).get('ref'),
                    subfolder=config['source'].get('git_config', {}).get('subfolder')
                )
                
                variables, warnings, errors = parser.get_variables()
                
                # Log any warnings or errors
                for warning in warnings:
                    logger.warning(f"⚠️ Warning for {module_name}: {warning}")
                for error in errors:
                    logger.error(f"❌ Error for {module_name}: {error}")
                
                if not variables:
                    logger.warning(f"⚠️ No variables found for module {module_name}")
                    continue
                
                # Create tools for this module
                module_tools = create_terraform_tools(module_name, config, variables)
                tools.extend(module_tools)
                logger.info(f"✅ Successfully created tools for {module_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load module from {filename}: {str(e)}", exc_info=True)
                continue

    return tools

# Export the loader function
__all__ = ['load_terraform_tools'] 