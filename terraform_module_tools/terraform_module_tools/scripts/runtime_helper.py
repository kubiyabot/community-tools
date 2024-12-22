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
            
        # If auto_discover is false, we should have instructions
        if not config.get('auto_discover', True):
            if not config.get('instructions'):
                logger.warning("Manual configuration mode but no instructions provided")
                return None
                
            # Get instructions from teammate
            chat_client = KubiyaChatClient()
            result = chat_client.send_message(
                f"I need help with the following Terraform module:\n\n"
                f"Instructions: {config['instructions']}\n\n"
                f"This module has the following variables:\n"
                + "\n".join([
                    f"- {var_name}: {var_config.get('description', 'No description')}"
                    for var_name, var_config in config.get('variables', {}).items()
                ])
                + "\n\nPlease provide specific guidance for this use case."
            )
            
            if 'error' in result:
                logger.error(f"Failed to get runtime instructions: {result['error']}")
                return None
                
            return result.get('response')
        
        # For auto-discovered modules, use regular instructions if available
        return None if not config.get('instructions') else config['instructions']
            
    except Exception as e:
        logger.error(f"Failed to get runtime instructions: {str(e)}")
        return None 