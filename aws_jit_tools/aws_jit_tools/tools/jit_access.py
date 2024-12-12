from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec, Arg
from pathlib import Path
from .base import AWSJITTool
from ..scripts.config_loader import get_access_configs, get_s3_configs
import json
import uuid
from datetime import datetime, timedelta
import logging
import re

# Get access handler code
HANDLER_PATH = Path(__file__).parent.parent / 'scripts' / 'access_handler.py'
with open(HANDLER_PATH) as f:
    HANDLER_CODE = f.read()

# Initialize tools dictionary at module level
tools = {}
s3_tools = {}

class S3JITAccess(AWSJITTool):
    def __init__(self, role_arn):
        super().__init__(role_arn)
        self.sso_client = self.session.client('sso-admin')
        self.iam_client = self.session.client('iam')
        self.logger = logging.getLogger(__name__)
        
    def _parse_iso8601_duration(self, duration_str):
        """Parse ISO8601 duration string to timedelta"""
        pattern = re.compile(r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        if not match:
            raise ValueError(f"Invalid ISO8601 duration format: {duration_str}")
        
        days, hours, minutes, seconds = match.groups()
        return timedelta(
            days=int(days or 0),
            hours=int(hours or 0),
            minutes=int(minutes or 0),
            seconds=int(seconds or 0)
        )

    def _validate_duration(self, requested_duration, max_duration):
        """Validate the requested duration against maximum allowed"""
        try:
            requested = self._parse_iso8601_duration(requested_duration)
            maximum = self._parse_iso8601_duration(max_duration)
            
            if requested > maximum:
                raise ValueError(f"Requested duration exceeds maximum allowed ({max_duration})")
            
            return requested_duration
        except ValueError as e:
            raise ValueError(f"Invalid duration format: {e}")

    def _create_permission_set(self, instance_arn, name, description, session_duration, policy_doc):
        """Create a new permission set with inline policy"""
        try:
            # Create permission set
            response = self.sso_client.create_permission_set(
                InstanceArn=instance_arn,
                Name=f"kubiya-{name}-{uuid.uuid4().hex[:8]}",
                Description=description,
                SessionDuration=session_duration,
                Tags=[
                    {
                        'Key': 'ManagedBy',
                        'Value': 'Kubiya'
                    },
                    {
                        'Key': 'CreatedAt',
                        'Value': datetime.utcnow().isoformat()
                    }
                ]
            )
            
            permission_set_arn = response['PermissionSet']['PermissionSetArn']
            
            # Put inline policy
            self.sso_client.put_inline_policy_to_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
                InlinePolicy=json.dumps(policy_doc)
            )
            
            return permission_set_arn
            
        except Exception as e:
            print(f"Error creating permission set: {e}")
            raise

    def _load_config(self, config_name):
        """Load and validate S3 access configuration"""
        configs = get_s3_configs()
        if config_name not in configs:
            raise ValueError(f"Configuration '{config_name}' not found")
        return configs[config_name]

    def grant_access(self, config_name, requester_id, duration=None):
        """Grant S3 access by creating and assigning permission set"""
        try:
            # Load and validate configuration
            config = self._load_config(config_name)
            
            # Validate duration
            duration = self._validate_duration(
                duration or config['session_duration'],
                config['session_duration']
            )

            # Get SSO instance
            instances = self.sso_client.list_instances()
            if not instances['Instances']:
                raise Exception("No SSO instance found")
            
            instance_arn = instances['Instances'][0]['InstanceArn']
            
            # Generate policy document
            policy_doc = self._generate_policy(config)
            
            # Create permission set with tags
            permission_set_arn = self._create_permission_set(
                instance_arn,
                config['name'],
                config['description'],
                duration,
                policy_doc
            )
            
            self.logger.info(f"Created permission set: {permission_set_arn}")
            
            # Create account assignments
            created_assignments = []
            try:
                accounts = set(bucket['account_id'] for bucket in config['buckets'])
                for account_id in accounts:
                    response = self.sso_client.create_account_assignment(
                        InstanceArn=instance_arn,
                        TargetId=account_id,
                        TargetType='AWS_ACCOUNT',
                        PermissionSetArn=permission_set_arn,
                        PrincipalType='USER',
                        PrincipalId=requester_id
                    )
                    created_assignments.append({
                        'account_id': account_id,
                        'request_id': response['RequestId']
                    })
                    self.logger.info(f"Created assignment for account {account_id}")
            except Exception as e:
                # Cleanup partial assignments if something fails
                self.logger.error(f"Error creating assignments: {e}")
                self._cleanup_failed_grant(instance_arn, permission_set_arn, created_assignments, requester_id)
                raise
            
            return {
                'status': 'success',
                'permission_set_arn': permission_set_arn,
                'instance_arn': instance_arn,
                'assignments': created_assignments
            }
            
        except Exception as e:
            self.logger.error(f"Error granting access: {e}")
            raise

    def _cleanup_failed_grant(self, instance_arn, permission_set_arn, assignments, requester_id):
        """Clean up resources after failed grant attempt"""
        for assignment in assignments:
            try:
                self.sso_client.delete_account_assignment(
                    InstanceArn=instance_arn,
                    TargetId=assignment['account_id'],
                    TargetType='AWS_ACCOUNT',
                    PermissionSetArn=permission_set_arn,
                    PrincipalType='USER',
                    PrincipalId=requester_id
                )
            except Exception as e:
                self.logger.error(f"Error cleaning up assignment: {e}")

        try:
            self.sso_client.delete_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn
            )
        except Exception as e:
            self.logger.error(f"Error cleaning up permission set: {e}")

    def revoke_access(self, permission_set_arn, instance_arn, requester_id):
        """Revoke access by removing assignments and permission set"""
        try:
            # List account assignments
            assignments = self.sso_client.list_account_assignments(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn
            )
            
            # Delete account assignments
            for assignment in assignments['AccountAssignments']:
                if assignment['PrincipalId'] == requester_id:
                    self.sso_client.delete_account_assignment(
                        InstanceArn=instance_arn,
                        TargetId=assignment['AccountId'],
                        TargetType='AWS_ACCOUNT',
                        PermissionSetArn=permission_set_arn,
                        PrincipalType='USER',
                        PrincipalId=requester_id
                    )
            
            # Delete permission set
            self.sso_client.delete_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn
            )
            
            return {
                'status': 'success',
                'message': 'Access revoked successfully'
            }
            
        except Exception as e:
            print(f"Error revoking access: {e}")
            raise

    def _generate_policy(self, config):
        """Generate S3 bucket policy from template"""
        policy = config['policy_template']
        
        # Replace bucket name placeholders for each bucket
        resources = []
        for bucket in config['buckets']:
            bucket_name = bucket['name']  # Extract the name from the bucket dict
            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            resources.extend([bucket_arn, f"{bucket_arn}/*"])
            
        policy['Statement'][0]['Resource'] = resources
        return policy

def create_jit_tool(config, action):
    """Create a JIT tool from configuration."""
    args = []
    
    if action == "revoke":
        args.append(
            Arg(name="user_email", description="The email of the user to revoke access for", type="str")
        )
    elif action == "grant":
        args.append(
            Arg(name="duration", 
                description=f"Duration for the access token to be valid (maximum {config['session_duration']}) - needs to be in ISO8601 format eg: 'PT1H'", 
                type="str", 
                # This is the recommended duration for the access token (controlled on scripts/config) - does not guarantee the duration
                default=config['session_duration'])
        )

    # Define file specifications for all necessary files
    file_specs = [
        FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE),
        FileSpec(destination="/opt/scripts/utils/aws_utils.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'aws_utils.py').read()),
        FileSpec(destination="/opt/scripts/utils/notifications.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'notifications.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_client.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_client.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_messages.py').read()),
        FileSpec(destination="/opt/scripts/utils/webhook_handler.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'webhook_handler.py').read()),
    ]

    mermaid_diagram = f"""
    sequenceDiagram
        participant U as 👤 User
        participant T as 🛠️ Tool
        participant I as 🔍 IAM Identity Center
        participant S as 🔐 SSO Admin
        participant N as 📧 Notifications

        U->>+T: {"Request Access" if action == "grant" else "Request Revocation"}
        T->>+I: 🔎 Find User by Email
        I-->>-T: 📄 User Details
        T->>+S: 🔑 Get Permission Set: {config['permission_set']}
        S-->>-T: 🆔 Permission Set ARN
        T->>+S: { "🔧 Create Assignment" if action == "grant" else "❌ Delete Assignment" }
        Note over T,S: Account: {config['account_id']}
        S-->>-T: { "✅ Assignment Created" if action == "grant" else "🔓 Assignment Deleted" }
        T->>+N: Send Notification
        N-->>-T: Notification Sent
        T-->>-U: { "Access Granted 🎉" if action == "grant" else "Access Revoked 🔒" }
    """

    action_prefix = "jit_session_" + ("grant_" if action == "grant" else "revoke_")
    tool_name = f"{action_prefix}{config['name'].lower().replace(' ', '_')}"

    return AWSJITTool(
        name=tool_name,
        description=f"{config['description']} ({action.capitalize()}) - {'Grants' if action == 'grant' else 'Revokes'} access to AWS account {config['account_id']} using {config['permission_set']} permission set",
        args=args,
        content=f"""#!/bin/bash
set -e
echo ">> Processing request... ⏳"

# Install dependencies only if not found
python -c "import boto3, requests, jinja2, jsonschema, argparse" 2>/dev/null || pip install -q boto3 requests jinja2 jsonschema argparse > /dev/null 2>&1

export AWS_ACCOUNT_ID="{config['account_id']}"
export PERMISSION_SET_NAME="{config['permission_set']}"
export MAX_DURATION="{config['session_duration']}"

# Create __init__ files to cover the python project
touch /opt/scripts/__init__.py
touch /opt/scripts/utils/__init__.py

# Run access handler
echo ">> Just a moment... ⏳"
python /opt/scripts/access_handler.py {action} {"--user-email $KUBIYA_USER_EMAIL" if action == "grant" else "--user-email {{.user_email}}"} {"--duration {{.duration}}" if action == "grant" else "--duration PT1H"}
""",
        with_files=file_specs,
        mermaid=mermaid_diagram
    )

def create_s3_jit_tool(config, action):
    """Create a JIT tool for S3 bucket access from configuration."""
    args = []
    
    if action == "revoke":
        args.append(
            Arg(name="user_email", description="The email of the user to revoke access for", type="str")
        )
    elif action == "grant":
        args.append(
            Arg(name="duration", 
                description=f"Duration for the access (maximum {config['session_duration']}) - ISO8601 format (e.g., 'PT1H')", 
                type="str", 
                default=config['session_duration'])
        )

    # Define file specifications for all necessary files
    file_specs = [
        FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE),
        FileSpec(destination="/opt/scripts/utils/aws_utils.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'aws_utils.py').read()),
        FileSpec(destination="/opt/scripts/utils/notifications.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'notifications.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_client.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_client.py').read()),
        FileSpec(destination="/opt/scripts/utils/slack_messages.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'slack_messages.py').read()),
        FileSpec(destination="/opt/scripts/utils/webhook_handler.py", content=open(Path(__file__).parent.parent / 'scripts' / 'utils' / 'webhook_handler.py').read()),
    ]

    # Get list of bucket names for display and script
    bucket_names = [bucket['name'] for bucket in config['buckets']]
    buckets_list = ", ".join(bucket_names)

    tool_name = f"s3_{action}_{config['name'].lower().replace(' ', '_')}"

    mermaid_diagram = f"""
    sequenceDiagram
        participant U as 👤 User
        participant T as 🛠️ Tool
        participant I as 🔍 IAM
        participant B as 🪣 S3 Bucket
        participant N as 📧 Notifications
        participant W as ⏰ Webhook

        U->>+T: {"Request S3 Access" if action == "grant" else "Request Access Removal"}
        T->>+I: 🔎 Find User by Email
        I-->>-T: 📄 User Details
        T->>+B: {"🔧 Update Bucket Policy" if action == "grant" else "❌ Remove from Policy"}
        Note over T,B: Buckets: {buckets_list}
        B-->>-T: {"✅ Access Granted" if action == "grant" else "🔓 Access Removed"}
        T->>+N: Send Notification
        N-->>-T: Notification Sent
        {"T->>+W: Schedule Revocation" if action == "grant" else ""}
        {"W-->>-T: Scheduled" if action == "grant" else ""}
        T-->>-U: {"S3 Access Granted 🎉" if action == "grant" else "S3 Access Revoked 🔒"}
    """

    return AWSJITTool(
        name=tool_name,
        description=f"{config['description']} ({action.capitalize()}) - {'Grants' if action == 'grant' else 'Revokes'} access to S3 buckets: {buckets_list}",
        args=args,
        content=f"""#!/bin/bash
set -e
echo ">> Processing request... ⏳"

# Install dependencies
pip install -q boto3 requests jinja2 jsonschema argparse

# Export bucket names and policy template from config
export BUCKETS="{','.join(bucket_names)}"
export POLICY_TEMPLATE='{json.dumps(config['policy_template'])}'
export MAX_DURATION="{config['session_duration']}"

touch /opt/scripts/__init__.py
touch /opt/scripts/utils/__init__.py

# Run access handler for each bucket in the configuration
for bucket in {' '.join(bucket_names)}; do
    echo "Processing bucket: $bucket"
    python /opt/scripts/access_handler.py {action} --user-email {"$KUBIYA_USER_EMAIL" if action == "grant" else "{{.user_email}}"} --bucket-name "$bucket" {"--duration {{.duration}}" if action == "grant" else ""}
done
""",
        with_files=file_specs,
        mermaid=mermaid_diagram,
        long_running=False,
    )

# Load configurations and create tools
try:
    ACCESS_CONFIGS = get_access_configs()
    S3_ACCESS_CONFIGS = get_s3_configs()

    # Create and register tools
    for action in ["grant", "revoke"]:
        for access_type, config in ACCESS_CONFIGS.items():
            tool = create_jit_tool(config, action)
            tools[tool.name] = tool
            tool_registry.register("aws_jit", tool)

        for access_type, config in S3_ACCESS_CONFIGS.items():
            tool = create_s3_jit_tool(config, action)
            s3_tools[tool.name] = tool
            tool_registry.register("aws_jit", tool)

except Exception as e:
    print(f"Error loading configurations: {e}")
    raise

# Export all tools
__all__ = ['tools', 's3_tools'] 
