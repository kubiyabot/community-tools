import logging
from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_tools():
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
                    "KUBIYA_USER_EMAIL" 
                ],
                secrets=["SLACK_API_TOKEN"]
            )
            
            tools.append(tool)
            logger.info(f"Created tool: {tool.name}")

        return tools
        
    except Exception as e:
        logger.error(f"Error generating tools: {str(e)}")
        raise

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        logger.info("Generating AWS JIT access tools...")
        tools = generate_tools()
        
        # Register each tool
        for tool in tools:
            tool_registry.register("aws_jit", tool)
            logger.info(f"Registered tool: {tool.name}")
            
        logger.info(f"Successfully initialized {len(tools)} tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'generate_tools', 'AWSJITTool']