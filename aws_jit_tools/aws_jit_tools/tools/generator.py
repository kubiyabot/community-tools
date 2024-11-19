import logging
import json
import inspect
from pathlib import Path
from typing import List
from kubiya_sdk.tools import FileSpec
from kubiya_sdk.tools.registry import tool_registry
from ..tools.base import AWSJITTool

logger = logging.getLogger(__name__)

class ToolGenerator:
    """Generator for AWS JIT access tools."""
    def __init__(self):
        """Initialize the tool generator with configuration."""
        self.config = self._load_config()
        if not self.config:
            logger.error("Failed to load configuration")
            raise Exception("Failed to load configuration, could not generate tools")
        logger.info(f"Loaded configuration with {len(self.config.get('tools', {}))} tools")

    def _load_config(self) -> dict:
        """Load tool configuration from JSON."""
        try:
            config_path = Path(__file__).resolve().parent.parent.parent / 'aws_jit_config.json'
            logger.info(f"Loading config from: {config_path}")
            if not config_path.exists():
                logger.error(f"Config file not found at {config_path}")
                raise Exception(f"Config file not found at {config_path}")
            with open(config_path) as f:
                config = json.load(f)
                logger.info("Successfully loaded config")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise

    def generate_tools(self) -> List:
        """Generate tools based on configuration."""
        tools = []
        try:
            for tool_id, config in self.config.get('tools', {}).items():
                logger.info(f"Generating tool for: {tool_id}")
                tool = self._create_tool(tool_id, config)
                if tool:
                    tools.append(tool)
                    # Register the tool immediately
                    tool_registry.register("aws_jit", tool)
                    logger.info(f"Successfully registered tool: {tool.name}")

            logger.info(f"Generated and registered {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error generating tools: {str(e)}")
            raise

    def _create_tool(self, tool_id: str, config: dict):
        """Create individual tool based on configuration."""
        try:
            # Delayed import to avoid circular dependency
            from aws_jit_tools.tools.base import AWSJITTool

            # Read access_handler.py content directly
            access_handler_path = Path(__file__).resolve().parent.parent / 'scripts' / 'access_handler.py'
            with open(access_handler_path, 'r') as f:
                access_handler_code = f.read()

            content = f"""
#!/bin/bash
set -e

echo "Installing required packages..."
apk add --no-cache python3 py3-pip
pip3 install boto3 requests

echo "Setting environment variables..."
export AWS_ACCOUNT_ID="{config['account_id']}"
export PERMISSION_SET_NAME="{config['permission_set']}"
export SESSION_DURATION="{config.get('session_duration', 'PT1H')}"

echo "Executing access handler..."
python3 /opt/scripts/access_handler.py
"""

            tool = AWSJITTool(
                name=f"jit_{tool_id.lower()}",
                description=config['description'],
                content=content,
                with_files=[
                    FileSpec(
                        destination="/opt/scripts/access_handler.py",
                        content=access_handler_code
                    )
                ],
                env=[
                    "AWS_PROFILE",
                    "KUBIYA_USER_EMAIL",
                    "AWS_ACCOUNT_ID",
                    "PERMISSION_SET_NAME"
                ]
            )
            return tool
        except Exception as e:
            logger.error(f"Error creating tool {tool_id}: {str(e)}")
            return None 