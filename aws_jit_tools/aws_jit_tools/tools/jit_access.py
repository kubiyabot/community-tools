from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool

# SE Access Tool
se_access = AWSJITTool(
    name="jit_se_access",
    description="Grants SE (Solutions Engineer) access to AWS account",
    content="""#!/bin/bash
set -e

export AWS_ACCOUNT_ID="876809951775"
export PERMISSION_SET_NAME="SE"
export SESSION_DURATION="PT1H"

pip install boto3 requests
python /opt/scripts/access_handler.py
""",
    mermaid="""
    sequenceDiagram
        participant U as User
        participant T as Tool
        participant I as IAM
        participant S as SSO

        U->>+T: Request SE Access
        T->>+I: Find/Create User
        I-->>-T: User Details
        T->>+S: Get Permission Set
        S-->>-T: Permission Set ARN
        T->>+S: Assign Permissions
        S-->>-T: Assignment Complete
        T-->>-U: Access Granted
    """
)

# Admin Access Tool
admin_access = AWSJITTool(
    name="jit_admin_access",
    description="Grants Admin access to AWS account",
    content="""#!/bin/bash
set -e

export AWS_ACCOUNT_ID="876809951775"
export PERMISSION_SET_NAME="Admin"
export SESSION_DURATION="PT1H"

pip install boto3 requests
python /opt/scripts/access_handler.py
""",
    mermaid="""
    sequenceDiagram
        participant U as User
        participant T as Tool
        participant I as IAM
        participant S as SSO

        U->>+T: Request Admin Access
        T->>+I: Find/Create User
        I-->>-T: User Details
        T->>+S: Get Permission Set
        S-->>-T: Permission Set ARN
        T->>+S: Assign Permissions
        S-->>-T: Assignment Complete
        T-->>-U: Access Granted
    """
)

# Developer Access Tool
developer_access = AWSJITTool(
    name="jit_developer_access",
    description="Grants Developer access to AWS account",
    content="""#!/bin/bash
set -e

export AWS_ACCOUNT_ID="876809951775"
export PERMISSION_SET_NAME="Developer"
export SESSION_DURATION="PT1H"

pip install boto3 requests
python /opt/scripts/access_handler.py
""",
    mermaid="""
    sequenceDiagram
        participant U as User
        participant T as Tool
        participant I as IAM
        participant S as SSO

        U->>+T: Request Developer Access
        T->>+I: Find/Create User
        I-->>-T: User Details
        T->>+S: Get Permission Set
        S-->>-T: Permission Set ARN
        T->>+S: Assign Permissions
        S-->>-T: Assignment Complete
        T-->>-U: Access Granted
    """
)

# Register all tools
tool_registry.register("aws_jit", se_access)
tool_registry.register("aws_jit", admin_access)
tool_registry.register("aws_jit", developer_access)

__all__ = ['se_access', 'admin_access', 'developer_access'] 