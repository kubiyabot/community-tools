import inspect
import logging
from pathlib import Path
from typing import Dict, Any, List
from kubiya_sdk.tools import FileSpec
from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError as e:
    logger.error(f"Failed to import yaml: {str(e)}")
    yaml = None

class ToolGenerator:
    def __init__(self):
        if not yaml:
            logger.error("yaml module not available - cannot generate tools")
            return
        
        from .. import scripts
        self.scripts = scripts
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load tool configuration from YAML."""
        try:
            config_path = Path(__file__).parent.parent.parent / 'aws_jit_config.yaml'
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {}

    def generate_tools(self) -> List[Any]:
        """Generate tools based on configuration."""
        if not hasattr(self, 'config'):
            logger.error("Configuration not loaded - missing dependencies")
            return []

        tools = []
        try:
            for tool_id, config in self.config.get('tools', {}).items():
                tool = self._create_tool(tool_id, config)
                if tool:
                    tools.append(tool)
                    # Register tool with jit_access_to_ prefix
                    self.tool_registry.register("aws_jit", tool)
        except Exception as e:
            logger.error(f"Error generating tools: {str(e)}")
        return tools

    def _create_tool(self, tool_id: str, config: Dict[str, Any]) -> Any:
        """Create individual tool based on configuration."""
        try:
            return self.AWSJITTool(
                name=f"jit_access_to_{tool_id}",
                description=config['description'],
                content=self._generate_tool_content(config),
                env=[
                    "AWS_PROFILE",
                    "KUBIYA_USER_EMAIL",
                    "KUBIYA_API_KEY",
                    "KUBIYA_USER_ORG",
                    "KUBIYA_AGENT_PROFILE"
                ],
                with_files=[
                    self.FileSpec(
                        destination="/opt/scripts/access_handler.py",
                        content=inspect.getsource(self.scripts.access_handler)
                    )
                ],
                mermaid=self._generate_mermaid(tool_id, config)
            )
        except Exception as e:
            logger.error(f"Error creating tool {tool_id}: {str(e)}")
            return None

    def _generate_tool_content(self, config: Dict[str, Any]) -> str:
        return f"""
#!/bin/bash
set -e

# Install required packages
apk add --no-cache python3 py3-pip
pip3 install boto3 pyyaml requests

# Execute Python script
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