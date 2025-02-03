import os
import json
import logging
from typing import Optional, Dict, Any
from .chat_client import KubiyaChatClient

logger = logging.getLogger(__name__)

def get_runtime_instructions(module_path: str) -> Optional[str]:
    """Get runtime instructions from teammate for the module."""
    try:
        # Check for module configuration file
        config_file = os.path.join(module_path, '.module_config.json')
        if not os.path.exists(config_file):
            return None
            
        # Load module configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Get instructions based on configuration mode
        instructions = config.get('instructions')
        if not instructions:
            return None

        # If using manual configuration, include variable information
        if not config.get('auto_discover', True):
            chat_client = KubiyaChatClient()
            result = chat_client.send_message(
                f"I need help with the following Terraform module:\n\n"
                f"Instructions: {instructions}\n\n"
                f"This module has the following variables:\n"
                + "\n".join([
                    f"- {var_name}: {var_config.get('description', 'No description')}"
                    + (f" (Required)" if var_config.get('required', False) else "")
                    + (f" (Default: {var_config['default']})" if 'default' in var_config else "")
                    for var_name, var_config in config.get('variables', {}).items()
                ])
                + "\n\nPlease provide specific guidance for this use case."
            )
            
            if 'error' in result:
                logger.error(f"Failed to get runtime instructions: {result['error']}")
                return None
                
            return result.get('response')
        
        # For auto-discovered modules, return the instructions directly
        return instructions
            
    except Exception as e:
        logger.error(f"Failed to get runtime instructions: {str(e)}")
        return None 