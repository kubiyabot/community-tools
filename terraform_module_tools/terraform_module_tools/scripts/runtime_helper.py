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
            
        if not config.get('instructions'):
            return None
            
        # Get instructions from teammate
        chat_client = KubiyaChatClient()
        result = chat_client.send_message(
            f"I need help with the following Terraform module:\n\n"
            f"Instructions: {config['instructions']}\n\n"
            f"Please provide specific guidance for this use case."
        )
        
        if 'error' in result:
            logger.error(f"Failed to get runtime instructions: {result['error']}")
            return None
            
        return result.get('response')
        
    except Exception as e:
        logger.error(f"Failed to get runtime instructions: {str(e)}")
        return None 