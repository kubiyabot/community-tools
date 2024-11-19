import inspect
from typing import List
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec

from .base import AWSIAMAccessTool
from .config import IAMAccessConfig
from . import scripts

def generate_iam_access_tools() -> List[AWSIAMAccessTool]:
    """Generate IAM access tools based on configuration."""
    config = IAMAccessConfig()
    tools = []

    for policy in config.policies:
        tool = AWSIAMAccessTool(
            name=f"grant_{policy.request_name.lower().replace(' ', '_')}_access",
            description=f"Grant {policy.request_name} access to AWS account {policy.aws_account_id}",
            content=f"""
import os
import sys
import json

# Set required environment variables
os.environ['AWS_POLICY_NAME'] = "{policy.policy_name}"
os.environ['AWS_ACCOUNT_ID'] = "{policy.aws_account_id}"

# Execute the management script
sys.path.append('/opt/scripts')
from manage_access import main

try:
    main()
except Exception as e:
    print(json.dumps({{"status": "error", "message": str(e)}}))
    sys.exit(1)
            """,
            args=[],
            env=["AWS_PROFILE", "KUBIYA_USER_EMAIL", "AWS_IAM_CONFIG_URL"],
            with_files=[
                FileSpec(
                    destination="/opt/scripts/manage_access.py",
                    content=inspect.getsource(scripts.manage_access)
                )
            ],
            mermaid=f"""
            sequenceDiagram
                participant U as User
                participant T as Tool
                participant I as IAM
                participant S as AWS SSO

                U->>+T: Request {policy.request_name} Access
                T->>+I: Find/Create User
                I-->>-T: User Details
                T->>+S: Get Permission Set
                S-->>-T: Permission Set ARN
                T->>+S: Assign Permissions
                S-->>-T: Assignment Complete
                T-->>-U: Access Granted
            """
        )
        tools.append(tool)

    return tools

# Generate and register tools
for tool in generate_iam_access_tools():
    tool_registry.register("aws", tool) 