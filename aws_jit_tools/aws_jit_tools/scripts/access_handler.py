import logging
import os
import sys
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import time
import threading

logger = logging.getLogger(__name__)

try:
    import boto3
except ImportError as e:
    logger.error(f"Failed to import boto3: {str(e)}")
    print(json.dumps({
        "status": "error",
        "error_type": "ImportError",
        "message": "Required package boto3 is not installed - please ignore this during discovery"
    }))
    pass

try:
    from jinja2 import Template, Environment, FileSystemLoader
except ImportError as e:
    logger.error(f"Failed to import jinja2: {str(e)}")
    print(json.dumps({
        "status": "error",
        "error_type": "ImportError",
        "message": "Required package jinja2 is not installed - please ignore this during discovery"
    }))
    pass

try:
    import argparse
except ImportError as e:
    logger.error(f"Failed to import argparse: {str(e)}")
    print(json.dumps({
        "status": "error",
        "error_type": "ImportError",
        "message": "Required package argparse is not installed - please ignore this during discovery"
    }))
    pass

from utils.notifications import NotificationManager
from utils.aws_utils import get_account_alias, get_permission_set_details
from utils.slack_messages import create_access_revoked_blocks
from utils.iam_policy_manager import IAMPolicyManager
from utils.webhook_handler import WebhookHandler

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
            self.policy_manager = IAMPolicyManager(self.session)
            self.webhook_handler = WebhookHandler()
            
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

    def validate_duration(self, requested_duration: str, max_duration: str) -> str:
        """Validate that requested duration doesn't exceed maximum duration."""
        try:
            requested_seconds = self.parse_iso8601_duration(requested_duration)
            max_seconds = self.parse_iso8601_duration(max_duration)
            
            if requested_seconds > max_seconds:
                print_progress(f"Requested duration exceeds maximum allowed duration of {max_duration}. Using maximum duration.", "⚠️")
                return max_duration
            
            return requested_duration
        except Exception as e:
            print_progress(f"Invalid duration format. Using default duration of {max_duration}", "⚠️")
            return max_duration

    def _handle_error(self, message: str, error: Exception):
        """Handle and log errors."""
        error_msg = f"{message}: {str(error)}"
        logger.error(error_msg)
        formatted_message = f"\n❌ Error: {message}\n   └─ Details: {str(error)}"
        print(formatted_message)
        sys.exit(1)

    def _create_and_attach_policy(self, user_name: str, policy_document: Dict[str, Any], purpose: str) -> Optional[str]:
        """Create and attach a policy to a user."""
        try:
            # Create policy
            policy_arn = self.policy_manager.create_policy(
                policy_document=policy_document,
                purpose=purpose,
                user_id=user_name
            )
            if not policy_arn:
                raise ValueError("Failed to create policy")

            # Attach policy to user
            if not self.policy_manager.attach_user_policy(user_name, policy_arn):
                # Cleanup if attach fails
                self.policy_manager.delete_policy(policy_arn)
                raise ValueError("Failed to attach policy")

            return policy_arn

        except Exception as e:
            logger.error(f"Failed to create and attach policy: {e}")
            return None

    def _cleanup_user_policies(self, user_name: str) -> bool:
        """Clean up all JIT policies for a user."""
        try:
            return self.policy_manager.cleanup_user_policies(user_name)
        except Exception as e:
            logger.error(f"Failed to cleanup user policies: {e}")
            return False

    def revoke_access(self, user_email: str, permission_set_name: str):
        """Revoke access for a user by email and permission set name."""
        try:
            print_progress(f"Revoking access for {user_email} with permission set {permission_set_name}...", "🔄")
            
            # Find user by email
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Clean up any JIT policies
            print_progress("Cleaning up IAM policies...", "🧹")
            self._cleanup_user_policies(user['UserName'])

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
                PrincipalId=user['UserId']
            )

            print_progress(f"Access revoked successfully for {user_email}", "✅")

            # Notify user
            self.notifications.send_access_revoked(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                permission_set=permission_set_name,
                user_email=user_email
            )

        except Exception as e:
            self._handle_error("Failed to revoke access", e)

    def _schedule_revocation_webhook(self, 
                                   user_email: str,
                                   duration_seconds: int,
                                   account_id: str,
                                   permission_set: Optional[str] = None,
                                   policy_details: Optional[Dict[str, Any]] = None,
                                   buckets: Optional[list] = None):
        """Schedule the revocation webhook after the TTL expires."""
        def send_webhook():
            time.sleep(duration_seconds)
            access_type = "s3" if buckets else "sso"
            self.webhook_handler.send_revocation_webhook(
                user_email=user_email,
                access_type=access_type,
                policy_details=policy_details or {},
                duration_seconds=duration_seconds,
                account_id=account_id,
                permission_set=permission_set,
                buckets=buckets
            )

        # Start webhook thread
        webhook_thread = threading.Thread(target=send_webhook)
        webhook_thread.daemon = True
        webhook_thread.start()

    def grant_access(self, user_email: str, permission_set_name: str, requested_duration: str, max_duration: str):
        """Grant access for a user by email and permission set name."""
        try:
            print_progress(f"Granting access for {user_email} with permission set {permission_set_name}...", "🔄")
            
            # Validate duration
            validated_duration = self.validate_duration(requested_duration, max_duration)
            duration_seconds = self.parse_iso8601_duration(validated_duration)
            
            # Find user by email
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Get permission set ARN
            permission_set_arn = self.get_permission_set_arn(permission_set_name)
            if not permission_set_arn:
                raise ValueError(f"Permission set not found: {permission_set_name}")
            
            # Get account alias and permission set details for better display
            account_alias = get_account_alias(self.session) or os.environ['AWS_ACCOUNT_ID']
            permission_set_details = get_permission_set_details(
                self.session, 
                self.instance_arn, 
                permission_set_arn
            )
            
            print_progress("Creating account assignment...", "⚙️")
            
            # Create assignment
            response = self.sso_admin.create_account_assignment(
                InstanceArn=self.instance_arn,
                TargetId=os.environ['AWS_ACCOUNT_ID'],
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=permission_set_arn,
                PrincipalType='USER',
                PrincipalId=user['UserId']
            )

            # Print human-readable success message
            print_progress(f"Access granted successfully!", "✅")
            print(f"   ├─ Account: {account_alias} ({os.environ['AWS_ACCOUNT_ID']})")
            print(f"   ├─ User: {user_email}")
            print(f"   ├─ Permission Set: {permission_set_name}")
            print(f"   └─ Duration: {duration_seconds/3600:.1f} hours")

            # Send notifications using the notification manager
            self.notifications.send_access_granted(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                account_alias=account_alias,
                permission_set=permission_set_name,
                permission_set_details=permission_set_details,
                duration_seconds=duration_seconds,
                user_email=user_email
            )

            # After successful access grant, schedule revocation webhook
            self._schedule_revocation_webhook(
                user_email=user_email,
                duration_seconds=duration_seconds,
                account_id=os.environ['AWS_ACCOUNT_ID'],
                permission_set=permission_set_name,
                policy_details={
                    "name": permission_set_name,
                    "type": "sso",
                    "details": permission_set_details
                }
            )

        except Exception as e:
            self._handle_error("Failed to grant access", e)

    def grant_s3_access(self, user_email: str, buckets: List[str], policy_template: str, duration: str):
        """Grant S3 access for a user."""
        try:
            print_progress(f"Granting S3 access for {user_email}...", "🔄")
            
            # Validate duration
            duration_seconds = self.parse_iso8601_duration(duration)
            
            # Find user by email
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Schedule revocation webhook
            self._schedule_revocation_webhook(
                user_email=user_email,
                duration_seconds=duration_seconds,
                account_id=os.environ['AWS_ACCOUNT_ID'],
                buckets=buckets,
                policy_details={
                    "name": f"s3_{policy_template.lower()}",
                    "type": "s3",
                    "template": policy_template,
                    "buckets": buckets
                }
            )

            # Print human-readable success message
            print_progress(f"S3 access granted successfully!", "✅")
            print(f"   ├─ Account: {os.environ['AWS_ACCOUNT_ID']}")
            print(f"   ├─ User: {user_email}")
            print(f"   ├─ Policy Template: {policy_template}")
            print(f"   └─ Duration: {duration_seconds/3600:.1f} hours")

            # Send notifications using the notification manager
            self.notifications.send_s3_access_granted(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                user_email=user_email,
                policy_template=policy_template,
                duration_seconds=duration_seconds
            )

        except Exception as e:
            self._handle_error("Failed to grant S3 access", e)

def main():
    """Main function to handle command line arguments and execute actions."""
    parser = argparse.ArgumentParser(description='AWS Access Handler')
    parser.add_argument('action', choices=['grant', 'revoke'], help='Action to perform')
    parser.add_argument('--user-email', required=True, help='Email of the user')
    parser.add_argument('--duration', default='PT1H', help='Duration for access (ISO8601 format, e.g., PT1H)')
    
    args = parser.parse_args()
    
    print_progress("Starting AWS Access Handler...", "🚀")
    
    try:
        handler = AWSAccessHandler()
        
        if args.action == 'grant':
            print_progress(f"Granting access for user: {args.user_email}", "🔑")
            handler.grant_access(
                user_email=args.user_email,
                permission_set_name=os.environ.get('PERMISSION_SET_NAME', 'DefaultPermissionSet'),
                requested_duration=args.duration,
                max_duration=os.environ.get('MAX_DURATION', 'PT1H')
            )
        else:  # revoke
            print_progress(f"Revoking access for user: {args.user_email}", "🔒")
            handler.revoke_access(
                user_email=args.user_email,
                permission_set_name=os.environ.get('PERMISSION_SET_NAME', 'DefaultPermissionSet')
            )
            
    except Exception as e:
        print_progress(f"Error: {str(e)}", "❌")
        sys.exit(1)

if __name__ == '__main__':
    main()

# Export the class
__all__ = ['AWSAccessHandler']
