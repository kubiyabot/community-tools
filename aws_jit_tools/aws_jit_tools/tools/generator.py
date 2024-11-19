import inspect
from pathlib import Path
from typing import Dict, Any, List
import yaml
from kubiya_sdk.tools import FileSpec
from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool
from .. import scripts

class ToolGenerator:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load tool configuration from YAML."""
        config_path = Path(__file__).parent.parent.parent / 'aws_jit_config.yaml'
        with open(config_path) as f:
            return yaml.safe_load(f)

    def generate_tools(self) -> List[AWSJITTool]:
        """Generate tools based on configuration."""
        tools = []
        for tool_id, config in self.config['tools'].items():
            tool = self._create_tool(tool_id, config)
            tools.append(tool)
            # Register tool with jit_access_to_ prefix
            tool_registry.register("aws_jit", tool)
        return tools

    def _create_tool(self, tool_id: str, config: Dict[str, Any]) -> AWSJITTool:
        """Create individual tool based on configuration."""
        return AWSJITTool(
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
                FileSpec(
                    destination="/opt/scripts/access_handler.py",
                    content=inspect.getsource(scripts.access_handler)
                )
            ],
            mermaid=self._generate_mermaid(tool_id, config)
        )

    def _generate_tool_content(self, config: Dict[str, Any]) -> str:
        return f"""
import os
import sys

# Set required environment variables
os.environ['AWS_ACCOUNT_ID'] = "{config['account_id']}"
os.environ['PERMISSION_SET_NAME'] = "{config['permission_set']}"

# Execute access handler
sys.path.append('/opt/scripts')
from access_handler import main
main()
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