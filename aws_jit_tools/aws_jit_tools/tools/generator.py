import logging
import json
from pathlib import Path
from typing import List
from .base import AWSJITTool

logger = logging.getLogger(__name__)

def generate_tools() -> List[AWSJITTool]:
    """Generate AWS JIT access tools from configuration."""
    try:
        # Load config
        config_path = Path(__file__).resolve().parent.parent.parent / 'aws_jit_config.json'
        logger.info(f"Loading config from: {config_path}")
        
        with open(config_path) as f:
            config = json.load(f)

        tools = []
        for tool_id, tool_config in config.get('tools', {}).items():
            logger.info(f"Generating tool for: {tool_id}")
            
            # Create tool script content
            script = f"""#!/bin/bash
set -e

# Set environment variables
export AWS_ACCOUNT_ID="{tool_config['account_id']}"
export PERMISSION_SET_NAME="{tool_config['permission_set']}"
export SESSION_DURATION="{tool_config.get('session_duration', 'PT1H')}"

# Install dependencies
pip install boto3 requests

# Execute access handler
python /opt/scripts/access_handler.py
"""
            
            # Create tool
            tool = AWSJITTool(
                name=f"jit_{tool_id.lower()}",
                description=tool_config['description'],
                content=script,
                env=[
                    "AWS_PROFILE",
                    "KUBIYA_USER_EMAIL",
                    "SLACK_API_TOKEN"
                ]
            )
            
            tools.append(tool)
            logger.info(f"Created tool: {tool.name}")

        return tools
        
    except Exception as e:
        logger.error(f"Error generating tools: {str(e)}")
        raise

# Make generate_tools available at module level
__all__ = ['generate_tools']

# Ensure the function is available when imported
globals()['generate_tools'] = generate_tools