from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec
from ..tools.base import AWSJITTool
from pathlib import Path

# Get access handler code
HANDLER_PATH = Path(__file__).parent.parent / 'scripts' / 'access_handler.py'
with open(HANDLER_PATH) as f:
    HANDLER_CODE = f.read()

# Configuration for different access types
ACCESS_CONFIGS = {
    "Solution Engineer Access to Staging": {
        "name": "jit_se_access",
        "description": "Grants SE (Solutions Engineer) access to staging AWS account (876809951775)",
        "account_id": "876809951775",
        "permission_set": "SE",
        "session_duration": "PT1H"
    },
}

def create_jit_tool(config):
    """Create a JIT tool from configuration."""
    return AWSJITTool(
        name=config["name"],
        description=config["description"],
        content=f"""#!/bin/bash
set -e

export AWS_ACCOUNT_ID="{config['account_id']}"
export PERMISSION_SET_NAME="{config['permission_set']}"
export SESSION_DURATION="{config['session_duration']}"

pip install boto3 requests
python /opt/scripts/access_handler.py
""",
        with_files=[
            FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE)
        ],
        mermaid=f"""
    sequenceDiagram
        participant U as User
        participant T as Tool
        participant I as IAM
        participant S as SSO

        U->>+T: Request {config['permission_set']} Access
        T->>+I: Find/Create User
        I-->>-T: User Details
        T->>+S: Get Permission Set
        S-->>-T: Permission Set ARN
        T->>+S: Assign Permissions
        S-->>-T: Assignment Complete
        T-->>-U: Access Granted
    """
    )

# Create tools from configuration
tools = {
    access_type: create_jit_tool(config)
    for access_type, config in ACCESS_CONFIGS.items()
}

# Register all tools
for tool in tools.values():
    tool_registry.register("aws_jit", tool)

# Export all tools
__all__ = list(tools.keys())
globals().update(tools) 