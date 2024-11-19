import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from kubiya_sdk.tools import FileSpec
from .base import AWSJITTool

logger = logging.getLogger(__name__)

class ToolGenerator:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load tool configuration from JSON."""
        try:
            config_path = Path(__file__).resolve().parent.parent.parent / 'aws_jit_config.json'
            logger.info(f"Loading config from: {config_path}")
            if not config_path.exists():
                logger.error(f"Config file not found at: {config_path}")
                return {}
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {}

    def generate_tools(self) -> List[Any]:
        """Generate tools based on configuration."""
        if not self.config or 'tools' not in self.config:
            logger.error("No tools configuration found in aws_jit_config.json")
            return []

        tools = []
        try:
            for tool_id, config in self.config['tools'].items():
                logger.info(f"Generating tool for: {tool_id}")
                tool = self._create_tool(tool_id, config)
                if tool:
                    tools.append(tool)
                    logger.info(f"Created tool: jit_access_to_{tool_id}")

            logger.info(f"Generated {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error generating tools: {str(e)}")
            return []

    def _create_tool(self, tool_id: str, config: Dict[str, Any]) -> Any:
        """Create individual tool based on configuration."""
        try:
            from aws_jit_tools.scripts.access_handler import AWSAccessHandler
            
            tool = AWSJITTool(
                name=f"jit_access_to_{tool_id}",
                description=config['description'],
                content=self._generate_tool_content(config),
                env=[
                    "AWS_PROFILE",      # AWS profile with required permissions
                    "KUBIYA_USER_EMAIL" # User email for SSO lookup
                ],
                with_files=[
                    FileSpec(
                        destination="/opt/scripts/access_handler.py",
                        content=inspect.getsource(AWSAccessHandler)
                    )
                ],
                mermaid=self._generate_mermaid(tool_id, config)
            )
            return tool
        except Exception as e:
            logger.error(f"Error creating tool {tool_id}: {str(e)}")
            return None

    def _generate_tool_content(self, config: Dict[str, Any]) -> str:
        return f"""
#!/bin/bash
set -e

# Install required packages silently
apk add --no-cache --quiet python3 py3-pip > /dev/null 2>&1
pip3 install --quiet boto3 > /dev/null 2>&1

# Set environment variables
export AWS_ACCOUNT_ID="{config['account_id']}"
export PERMISSION_SET_NAME="{config['permission_set']}"

# Execute access handler with engaging message
echo "🔐 Granting {config['permission_set']} access in AWS account {config['account_id']}..."
python3 /opt/scripts/access_handler.py
"""

    def _generate_mermaid(self, tool_id: str, config: Dict[str, Any]) -> str:
        return f"""
sequenceDiagram
    participant U as User
    participant T as Tool
    participant I as IAM Identity Center
    participant A as AWS Account

    U->>+T: Request {tool_id} access
    T->>+I: Find user by email
    I-->>-T: User found
    T->>+A: Assign permission set
    A-->>-T: Access granted
    T-->>-U: Access confirmed
""" 