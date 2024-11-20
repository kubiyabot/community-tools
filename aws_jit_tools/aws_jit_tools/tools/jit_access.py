from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec, Arg
from pathlib import Path
from .base import AWSJITTool
from ..scripts.config_loader import get_access_configs, get_s3_configs

# Get access handler code
HANDLER_PATH = Path(__file__).parent.parent / 'scripts' / 'access_handler.py'
with open(HANDLER_PATH) as f:
    HANDLER_CODE = f.read()

# Load configurations
try:
    ACCESS_CONFIGS = get_access_configs()
    S3_ACCESS_CONFIGS = get_s3_configs()
except Exception as e:
    print(f"Error loading configurations: {e}")
    ACCESS_CONFIGS = {}
    S3_ACCESS_CONFIGS = {}
    raise e

def create_jit_tool(config, action):
    """Create a JIT tool from configuration."""
    args = []
    
    if action == "revoke":
        args.append(
            Arg(name="User Email", description="The email of the user to revoke access for", type="str")
        )
    elif action == "grant":
        args.append(
            Arg(name="Duration (TTL)", description="Duration for the access token to be valid (defaults to 1 hour) - needs to be in ISO8601 format eg: 'PT1H'", type="str", default="PT1H")
        )

    # Define file specifications for all necessary files
    file_specs = [
        FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE),
        FileSpec(destination="/opt/scripts/__init__.py", content=""),
        FileSpec(destination="/opt/scripts/utils/__init__.py", content=""),
        FileSpec(destination="/opt/scripts/utils/aws_utils.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'aws_utils.py').read()),
        FileSpec(destination="/opt/scripts/utils/notifications.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'notifications.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_client.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_client.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_messages.py').read()),
    ]

    return AWSJITTool(
        name=f"{config['name']}_{action}",
        description=f"{config['description']} ({action.capitalize()})",
        args=args,
        content=f"""#!/bin/bash
set -e

# Install dependencies first
pip install -q boto3 requests jinja2 > /dev/null 2>&1

export AWS_ACCOUNT_ID="{config['account_id']}"
export PERMISSION_SET_NAME="{config['permission_set']}"

# Run access handler
echo ">> Processing request... ⏳"
python /opt/scripts/access_handler.py {action} --user-email $1
""",
        with_files=file_specs,
        mermaid=f"""
    sequenceDiagram
        participant U as 👤 User
        participant T as 🛠️ Tool
        participant I as 🔍 IAM
        participant S as 🔐 SSO

        U->>+T: Request {config['permission_set']} {action.capitalize()}
        T->>+I: 🔎 Find/Create User
        I-->>-T: 📄 User Details
        T->>+S: 🔑 Get Permission Set
        S-->>-T: 🆔 Permission Set ARN
        T->>+S: { "🔧 Assign Permissions" if action == "grant" else "❌ Revoke Permissions" }
        S-->>-T: { "✅ Assignment Complete" if action == "grant" else "🔓 Revocation Complete" }
        T-->>-U: Access {action.capitalize()}ed 🎉
    """
    )

def create_s3_jit_tool(config, action):
    """Create a JIT tool for S3 bucket access from configuration."""
    args = []
    
    if action == "revoke":
        args.append(
            Arg(name="User Email", description="The email of the user to revoke access for", type="str")
        )
    elif action == "grant":
        args.append(
            Arg(name="Duration (TTL)", description="Duration for the access token to be valid (defaults to 1 hour) - needs to be in ISO8601 format eg: 'PT1H'", type="str", default="PT1H")
        )

    # Define file specifications for all necessary files
    file_specs = [
        FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE),
        FileSpec(destination="/opt/scripts/__init__.py", content=""),
        FileSpec(destination="/opt/scripts/utils/__init__.py", content=""),
        FileSpec(destination="/opt/scripts/utils/aws_utils.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'aws_utils.py').read()),
        FileSpec(destination="/opt/scripts/utils/notifications.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'notifications.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_client.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_client.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_messages.py').read()),
    ]

    return AWSJITTool(
        name=f"{config['name']}_{action}",
        description=f"{config['description']} ({action.capitalize()})",
        args=args,
        content=f"""#!/bin/bash
set -e

# Install dependencies first
pip install -q boto3 requests jinja2 > /dev/null 2>&1

export BUCKETS="{','.join(config['buckets'])}"
export POLICY_TEMPLATE="{config['policy_template']}"

# Run access handler
echo ">> Processing request... ⏳"
python /opt/scripts/access_handler.py {action} --user-email $1
""",
        with_files=file_specs,
        mermaid=f"""
    sequenceDiagram
        participant U as 👤 User
        participant T as 🛠️ Tool
        participant I as 🔍 IAM
        participant S as 🔐 SSO

        U->>+T: Request {config['description']} {action.capitalize()}
        T->>+I: 🔎 Find/Create User
        I-->>-T: 📄 User Details
        T->>+S: 🔑 Get/Create Policy
        S-->>-T: 🆔 Policy ARN
        T->>+S: { "🔧 Attach Policy" if action == "grant" else "❌ Detach Policy" }
        S-->>-T: { "✅ Policy Attached" if action == "grant" else "🔓 Policy Detached" }
        T-->>-U: Access {action.capitalize()}ed 🎉
    """
    )

# Create tools only if configurations are loaded successfully
if ACCESS_CONFIGS and S3_ACCESS_CONFIGS:
    # Create tools from configuration for both grant and revoke actions
    tools = {
        f"{access_type}_{action}": create_jit_tool(config, action)
        for access_type, config in ACCESS_CONFIGS.items()
        for action in ["grant", "revoke"]
    }

    # Create S3 tools from configuration for both grant and revoke actions
    s3_tools = {
        f"{access_type}_{action}": create_s3_jit_tool(config, action)
        for access_type, config in S3_ACCESS_CONFIGS.items()
        for action in ["grant", "revoke"]
    }

    # Register all tools
    for tool in {**tools, **s3_tools}.values():
        tool_registry.register("aws_jit", tool)

    # Export all tools
    __all__ = list({**tools, **s3_tools}.keys())
    globals().update({**tools, **s3_tools})
else:
    logger.error("No tools created due to configuration loading errors") 