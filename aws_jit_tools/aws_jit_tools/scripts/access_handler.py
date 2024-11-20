import logging
import os
import sys
import json
from jinja2 import Template, Environment, FileSystemLoader
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    import boto3
except ImportError as e:
    logger.error(f"Failed to import boto3: {str(e)}")
    print(json.dumps({
        "status": "error",
        "error_type": "ImportError",
        "message": "Required package boto3 is not installed - its OK during discovery"
    }))
    pass

from .utils.notifications import NotificationManager
from .utils.aws_utils import get_account_alias, get_permission_set_details
from .utils.slack_messages import create_access_revoked_blocks

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()

class AWSAccessHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize AWS access handler."""
        try:
            print_progress("Initializing AWS handler...", "🔄")
            self.session = boto3.Session(profile_name=profile_name)
            self.identitystore = self.session.client('identitystore')
            self.sso_admin = self.session.client('sso-admin')
            self.notifications = NotificationManager()
            
            print_progress("Fetching SSO instance details...", "🔍")
            instances = self.sso_admin.list_instances()['Instances']
            if not instances:
                raise ValueError("No SSO instance found")
            self.instance_arn = instances[0]['InstanceArn']
            self.identity_store_id = instances[0]['IdentityStoreId']
            print_progress("AWS handler initialized successfully", "✅")
            
        except Exception as e:
            self._handle_error("Failed to initialize AWS handler", e)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user in IAM Identity Center by email."""
        try:
            print_progress(f"Looking up user: {email}", "👤")
            response = self.identitystore.list_users(
                IdentityStoreId=self.identity_store_id,
                Filters=[{
                    'AttributePath': 'UserName',
                    'AttributeValue': email
                }]
            )

            users = response.get('Users', [])
            if not users:
                print_progress(f"No user found with email: {email}", "❌")
                return None

            print_progress(f"Found user: {users[0].get('UserName')}", "✅")
            return users[0]

        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            raise

    def get_permission_set_arn(self, permission_set_name: str) -> Optional[str]:
        """Get Permission Set ARN from its name."""
        try:
            print_progress(f"Looking up permission set: {permission_set_name}", "🔑")
            paginator = self.sso_admin.get_paginator('list_permission_sets')
            
            for page in paginator.paginate(InstanceArn=self.instance_arn):
                for permission_set_arn in page['PermissionSets']:
                    response = self.sso_admin.describe_permission_set(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn
                    )
                    if response['PermissionSet']['Name'] == permission_set_name:
                        print_progress(f"Found permission set: {permission_set_name}", "✅")
                        return permission_set_arn
            
            print_progress(f"No permission set found with name: {permission_set_name}", "❌")
            return None

        except Exception as e:
            logger.error(f"Error finding permission set by name: {str(e)}")
            raise

    def parse_iso8601_duration(self, duration: str) -> int:
        """Convert ISO8601 duration to seconds."""
        try:
            if duration.startswith('PT'):
                value = int(duration[2:-1])
                unit = duration[-1]
                if unit == 'H':
                    return value * 3600
                elif unit == 'M':
                    return value * 60
            return 3600  # Default 1 hour
        except Exception:
            return 3600

    def _handle_error(self, message: str, error: Exception):
        """Handle and log errors."""
        error_msg = f"{message}: {str(error)}"
        logger.error(error_msg)
        formatted_message = f"\n❌ Error: {message}\n   └─ Details: {str(error)}"
        print(formatted_message)
        sys.exit(1)

    def get_aws_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find AWS user in IAM Identity Center by email."""
        try:
            print_progress(f"Looking up AWS user: {email}", "👤")
            response = self.identitystore.list_users(
                IdentityStoreId=self.identity_store_id,
                Filters=[{
                    'AttributePath': 'UserName',
                    'AttributeValue': email
                }]
            )

            users = response.get('Users', [])
            if not users:
                print_progress(f"No AWS user found with email: {email}", "❌")
                return None

            print_progress(f"Found AWS user: {users[0].get('UserName')}", "✅")
            return users[0]

        except Exception as e:
            logger.error(f"Error finding AWS user by email: {str(e)}")
            raise

    def revoke_access(self, user_email: str, permission_set_name: str):
        """Revoke access for a user by email and permission set name."""
        try:
            print_progress(f"Revoking access for {user_email} with permission set {permission_set_name}...", "🔄")

            # Find AWS user by email
            aws_user = self.get_aws_user_by_email(user_email)
            if not aws_user:
                raise ValueError(f"AWS user not found: {user_email}")

            # Get permission set ARN
            permission_set_arn = self.get_permission_set_arn(permission_set_name)
            if not permission_set_arn:
                raise ValueError(f"Permission set not found: {permission_set_name}")

            # Revoke account assignment
            response = self.sso_admin.delete_account_assignment(
                InstanceArn=self.instance_arn,
                TargetId=os.environ['AWS_ACCOUNT_ID'],
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=permission_set_arn,
                PrincipalType='USER',
                PrincipalId=aws_user['UserId']
            )

            print_progress(f"Access revoked successfully for {user_email}", "✅")

            # Notify user via Slack
            slack_user_id = self.notifications.slack.lookup_user_by_email(user_email)
            if slack_user_id:
                blocks = create_access_revoked_blocks(
                    account_id=os.environ['AWS_ACCOUNT_ID'],
                    permission_set=permission_set_name,
                    user_email=user_email
                )
                self.notifications.slack.send_message(
                    message="Your AWS access has been revoked.",
                    blocks=blocks
                )

        except Exception as e:
            self._handle_error("Failed to revoke access", e)

class S3AccessHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize S3 access handler."""
        try:
            print_progress("Initializing S3 handler...", "🔄")
            self.session = boto3.Session(profile_name=profile_name)
            self.iam = self.session.client('iam')
            self.notifications = NotificationManager()
            self.template_env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
            print_progress("S3 handler initialized successfully", "✅")
        except Exception as e:
            self._handle_error("Failed to initialize S3 handler", e)

    def _handle_error(self, message: str, error: Exception):
        """Handle and log errors."""
        error_msg = f"{message}: {str(error)}"
        logger.error(error_msg)
        formatted_message = f"\n❌ Error: {message}\n   └─ Details: {str(error)}"
        print(formatted_message)
        sys.exit(1)

    def create_policy(self, policy_name: str, buckets: list, template_name: str) -> str:
        """Create a policy for S3 bucket access."""
        try:
            print_progress(f"Creating policy: {policy_name}", "🔧")
            policy_template = self.template_env.get_template(template_name)
            policy_document = policy_template.render(buckets=buckets)

            response = self.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_document
            )
            policy_arn = response['Policy']['Arn']
            print_progress(f"Policy created: {policy_arn}", "✅")
            return policy_arn

        except Exception as e:
            self._handle_error("Failed to create policy", e)

    def attach_policy(self, user_name: str, policy_arn: str):
        """Attach a policy to a user."""
        try:
            print_progress(f"Attaching policy {policy_arn} to user {user_name}", "🔗")
            self.iam.attach_user_policy(
                UserName=user_name,
                PolicyArn=policy_arn
            )
            print_progress(f"Policy attached to user {user_name}", "✅")
        except Exception as e:
            self._handle_error("Failed to attach policy", e)

    def revoke_policy(self, user_name: str, policy_arn: str):
        """Detach a policy from a user."""
        try:
            print_progress(f"Detaching policy {policy_arn} from user {user_name}", "🔗")
            self.iam.detach_user_policy(
                UserName=user_name,
                PolicyArn=policy_arn
            )
            print_progress(f"Policy detached from user {user_name}", "✅")
        except Exception as e:
            self._handle_error("Failed to detach policy", e)

def main():
    """Main execution function."""
    try:
        action = os.environ.get('ACTION', 'grant')  # Default to 'grant' if not specified

        if action == 'grant':
            print_progress("Starting JIT access provisioning...", "🚀")

            # Get environment variables
            user_email = os.environ['KUBIYA_USER_EMAIL']
            account_id = os.environ['AWS_ACCOUNT_ID']
            permission_set = os.environ['PERMISSION_SET_NAME']
            session_duration = os.environ.get('SESSION_DURATION', 'PT1H')
            aws_profile = os.environ.get('AWS_PROFILE')

            handler = AWSAccessHandler(aws_profile)
            
            # Find user by email
            user = handler.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Get permission set ARN
            permission_set_arn = handler.get_permission_set_arn(permission_set)
            if not permission_set_arn:
                raise ValueError(f"Permission set not found: {permission_set}")
            
            # Get account alias and permission set details for better display
            account_alias = get_account_alias(handler.session) or account_id
            permission_set_details = get_permission_set_details(
                handler.session, 
                handler.instance_arn, 
                permission_set_arn
            )
            
            print_progress("Creating account assignment...", "⚙️")
            
            # Create assignment
            response = handler.sso_admin.create_account_assignment(
                InstanceArn=handler.instance_arn,
                TargetId=account_id,
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=permission_set_arn,
                PrincipalType='USER',
                PrincipalId=user['UserId']
            )

            # Get session duration in seconds
            duration_seconds = handler.parse_iso8601_duration(session_duration)
            
            # Print human-readable success message
            print_progress(f"Access granted successfully!", "✅")
            print(f"   ├─ Account: {account_alias} ({account_id})")
            print(f"   ├─ User: {user_email}")
            print(f"   ���─ Permission Set: {permission_set}")
            print(f"   └─ Duration: {duration_seconds/3600:.1f} hours")

            # Send notifications using the notification manager
            handler.notifications.send_access_granted(
                account_id=account_id,
                account_alias=account_alias,
                permission_set=permission_set,
                permission_set_details=permission_set_details,
                duration_seconds=duration_seconds,
                user_email=user_email
            )

        elif action == 'revoke':
            print_progress("Starting JIT access revocation to AWS...", "🚫")

            # Get environment variables
            user_email = sys.argv[2]  # Assuming user email is passed as the second argument
            permission_set = os.environ['PERMISSION_SET_NAME']
            aws_profile = os.environ.get('AWS_PROFILE')

            handler = AWSAccessHandler(aws_profile)
            handler.revoke_access(user_email, permission_set)

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        formatted_message = f"\n❌ Unexpected Error\n   └─ Details: {str(e)}"
        print(formatted_message)
        sys.exit(1)

if __name__ == "__main__":
    main()
