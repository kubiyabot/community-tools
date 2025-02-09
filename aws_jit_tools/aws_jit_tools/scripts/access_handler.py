import logging
import os
import sys
import json
from typing import Optional, Dict, Any, List
import time
import threading

# Add the parent directory to Python path to allow direct imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Direct imports from the scripts directory
from scripts.utils.notifications import NotificationManager
from scripts.utils.aws_utils import get_account_alias, get_permission_set_details
from scripts.utils.webhook_handler import WebhookHandler


def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()


def format_duration(seconds: int) -> str:
    """Format duration in seconds to a human-readable string."""
    if seconds >= 3600:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    elif seconds >= 60:
        minutes = seconds / 60
        return f"{int(minutes)} minutes"
    else:
        return f"{seconds} seconds"


class AWSAccessHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize AWS access handler."""
        try:
            print_progress("Initializing AWS handler...", "🔄")
            self.session = boto3.Session(profile_name=profile_name)
            self.identitystore = self.session.client('identitystore')
            self.sso_admin = self.session.client('sso-admin')
            self.notifications = NotificationManager()
            self.webhook_handler = WebhookHandler()
            self.iam_client = self.session.client('iam')

            print_progress("Fetching SSO instance details...", "🔍")
            instances = self.sso_admin.list_instances()['Instances']
            if not instances:
                raise ValueError("No SSO instance found")
            self.instance_arn = instances[0]['InstanceArn']
            self.identity_store_id = instances[0]['IdentityStoreId']
            print_progress("AWS handler initialized successfully", "✅")

        except Exception as e:
            self._handle_error("Failed to initialize AWS handler", e)

    def _handle_error(self, error_message: str, exception: Exception) -> None:
        """
        Handles an error by processing the given message and exception. This method
        is used internally to manage error-related operations within the system.

        Args:
            error_message (str): A descriptive message providing context about the error.
            exception (exception): The exception instance associated with the error.

        Returns:
            None
        """
        try:
            if isinstance(exception, self.sso_admin.exceptions.ConflictException):
                print_progress(f"{error_message}: Resource already exists", "⚠️")
                logger.warning(f"{error_message}: {str(exception)}")
                return

            if isinstance(exception, self.sso_admin.exceptions.ResourceNotFoundException):
                print_progress(f"{error_message}: Resource not found", "❌")
                logger.error(f"{error_message}: {str(exception)}")
                raise ValueError(f"{error_message}: Resource not found") from exception

            if isinstance(exception, self.sso_admin.exceptions.ValidationException):
                print_progress(f"{error_message}: Invalid input", "❌")
                logger.error(f"{error_message}: {str(exception)}")
                raise ValueError(f"{error_message}: {str(exception)}") from exception

            if isinstance(exception, self.sso_admin.exceptions.ThrottlingException):
                print_progress(f"{error_message}: Request throttled, please try again later", "⚠️")
                logger.warning(f"{error_message}: {str(exception)}")
                raise Exception(f"{error_message}: Request throttled") from exception

            # Handle AWS SSO specific exceptions
            if hasattr(self.sso_admin.exceptions, type(exception).__name__):
                print_progress(f"{error_message}: AWS SSO error occurred", "❌")
                logger.error(f"{error_message}: {str(exception)}")
                raise ValueError(f"{error_message}: {str(exception)}") from exception

            # Generic error handling
            print_progress(f"{error_message}: An unexpected error occurred", "❌")
            logger.error(f"{error_message}: {str(exception)}")
            raise Exception(f"{error_message}: {str(exception)}") from exception

        except Exception as e:
            logger.error(f"Error handling error: {e}")

    def revoke_permission_set(self, user_email: str, permission_set_name: str, delete_permission_set: bool = True):
        """
        Revoke access for a user and optionally delete the permission set.

        Args:
            user_email (str): User's email address
            permission_set_name (str): Name of the permission set
            delete_permission_set (bool): Whether to also delete the permission set after revoking access
        """
        try:
            print_progress(f"Revoking access for {user_email} with permission set {permission_set_name}...", "🔄")

            # Find user
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Get permission set ARN
            permission_set_arn = self.get_permission_set_arn(permission_set_name)
            if not permission_set_arn:
                raise ValueError(f"Permission set not found: {permission_set_name}")

            # Delete account assignment
            try:
                response = self.sso_admin.delete_account_assignment(
                    InstanceArn=self.instance_arn,
                    TargetId=os.environ['AWS_ACCOUNT_ID'],
                    TargetType='AWS_ACCOUNT',
                    PermissionSetArn=permission_set_arn,
                    PrincipalType='USER',
                    PrincipalId=user['UserId']
                )

                # Wait for deletion to complete
                status_response = self.sso_admin.describe_account_assignment_deletion_status(
                    InstanceArn=self.instance_arn,
                    AccountAssignmentDeletionRequestId=response['AccountAssignmentDeletionStatus']['RequestId']
                )
                while status_response['AccountAssignmentDeletionStatus']['Status'] == 'IN_PROGRESS':
                    time.sleep(2)
                    status_response = self.sso_admin.describe_account_assignment_deletion_status(
                        InstanceArn=self.instance_arn,
                        AccountAssignmentDeletionRequestId=response['AccountAssignmentDeletionStatus']['RequestId']
                    )

                if status_response['AccountAssignmentDeletionStatus']['Status'] != 'SUCCEEDED':
                    raise Exception(
                        f"Revocation failed: {status_response['AccountAssignmentDeletionStatus'].get('FailureReason')}")
            except self.sso_admin.exceptions.ResourceNotFoundException:
                print_progress("Account assignment already removed", "ℹ️")

            if delete_permission_set:
                print_progress("Cleaning up permission set...", "🧹")

                # Get attached managed policies
                try:
                    paginator = self.sso_admin.get_paginator('list_managed_policies_in_permission_set')
                    for page in paginator.paginate(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn
                    ):
                        for policy in page['AttachedManagedPolicies']:
                            try:
                                # Detach each managed policy
                                print_progress(f"Detaching policy: {policy['ManagedPolicyName']}", "🔄")
                                self.sso_admin.detach_managed_policy_from_permission_set(
                                    InstanceArn=self.instance_arn,
                                    PermissionSetArn=permission_set_arn,
                                    ManagedPolicyArn=policy['ManagedPolicyArn']
                                )
                            except Exception as e:
                                logger.error(f"Failed to detach policy {policy['ManagedPolicyName']}: {e}")
                except Exception as e:
                    logger.error(f"Failed to list managed policies: {e}")

                # Remove inline policy if exists
                try:
                    print_progress("Removing inline policy...", "🔄")
                    self.sso_admin.delete_inline_policy_from_permission_set(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn
                    )
                except self.sso_admin.exceptions.ResourceNotFoundException:
                    print_progress("No inline policy found", "ℹ️")
                except Exception as e:
                    logger.error(f"Failed to delete inline policy: {e}")

                # Delete the permission set
                try:
                    print_progress("Deleting permission set...", "🔄")
                    self.sso_admin.delete_permission_set(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn
                    )
                except Exception as e:
                    logger.error(f"Failed to delete permission set: {e}")

            print_progress(f"Access revoked successfully for {user_email}", "✅")
            if delete_permission_set:
                print_progress(f"Permission set {permission_set_name} deleted", "✅")

            # Notify user
            self.notifications.send_access_revoked(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                permission_set=permission_set_name,
                user_email=user_email
            )

        except Exception as e:
            self._handle_error("Failed to revoke access", e)

    def grant_permission_set(self,
                             user_email: str,
                             permission_set_name: str,
                             session_duration: str = "PT1H",
                             description: str = None,
                             relay_state: str = None,
                             inline_policy: Dict = None,
                             managed_policies: List[str] = None) -> Optional[str]:
        """
        Create a new permission set using AWS SSO Admin client and attach it to a user.

        Args:
            user_email (str): User's email address
            permission_set_name (str): Name for the new permission set
            session_duration (str): Session duration in ISO8601 format (default: PT1H)
            description (str): Description of the permission set
            relay_state (str): URL to redirect users to after signing in
            inline_policy (Dict): Inline policy document to attach
            managed_policies (List[str]): List of managed policy ARNs to attach

        Returns:
            Optional[str]: Permission set ARN if successful, None otherwise
        """
        try:
            print_progress(f"Creating permission set: {permission_set_name}", "🔄")

            # Check if permission set already exists
            try:
                paginator = self.sso_admin.get_paginator('list_permission_sets')
                for page in paginator.paginate(InstanceArn=self.instance_arn):
                    for permission_set_arn in page['PermissionSets']:
                        response = self.sso_admin.describe_permission_set(
                            InstanceArn=self.instance_arn,
                            PermissionSetArn=permission_set_arn
                        )
                        if response['PermissionSet']['Name'] == permission_set_name:
                            print_progress(f"Permission set {permission_set_name} already exists", "⚠️")
                            return permission_set_arn
            except Exception as e:
                logger.debug(f"Error checking existing permission set: {e}")

            # Create the permission set
            create_response = self.sso_admin.create_permission_set(
                Name=permission_set_name,
                InstanceArn=self.instance_arn,
                SessionDuration=session_duration,
                Description=description or f"Permission set for {permission_set_name}",
                RelayState=relay_state
            )

            permission_set_arn = create_response['PermissionSet']['PermissionSetArn']

            # Wait for permission set creation to complete
            waiter = self.sso_admin.get_waiter('permission_set_exists')
            waiter.wait(
                InstanceArn=self.instance_arn,
                PermissionSetArn=permission_set_arn
            )

            # Attach managed policies if provided
            if managed_policies:
                print_progress("Attaching managed policies...", "🔄")
                for policy_arn in managed_policies:
                    try:
                        self.sso_admin.attach_managed_policy_to_permission_set(
                            InstanceArn=self.instance_arn,
                            PermissionSetArn=permission_set_arn,
                            ManagedPolicyArn=policy_arn
                        )

                        # Wait for policy attachment to complete
                        self.sso_admin.get_waiter('permission_set_provisioned').wait(
                            InstanceArn=self.instance_arn,
                            PermissionSetArn=permission_set_arn
                        )
                    except self.sso_admin.exceptions.ConflictException:
                        print_progress(f"Policy {policy_arn} already attached", "ℹ️")
                    except Exception as e:
                        logger.error(f"Failed to attach policy {policy_arn}: {e}")

            # Attach inline policy if provided
            if inline_policy:
                print_progress("Attaching inline policy...", "🔄")
                try:
                    self.sso_admin.put_inline_policy_to_permission_set(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn,
                        InlinePolicy=json.dumps(inline_policy)
                    )
                    # Wait for inline policy provisioning
                    self.sso_admin.get_waiter('permission_set_provisioned').wait(
                        InstanceArn=self.instance_arn,
                        PermissionSetArn=permission_set_arn
                    )
                except Exception as e:
                    logger.error(f"Failed to attach inline policy: {e}")

            # Find user in Identity Store
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Provision the permission set before assignment
            try:
                self.sso_admin.provision_permission_set(
                    InstanceArn=self.instance_arn,
                    PermissionSetArn=permission_set_arn,
                    TargetType='AWS_ACCOUNT',
                    TargetId=os.environ['AWS_ACCOUNT_ID']
                )
                # Wait for provisioning to complete
                self.sso_admin.get_waiter('permission_set_provisioned').wait(
                    InstanceArn=self.instance_arn,
                    PermissionSetArn=permission_set_arn
                )
            except Exception as e:
                logger.error(f"Failed to provision permission set: {e}")

            print_progress("Creating account assignment...", "⚙️")
            try:
                assignment_response = self.sso_admin.create_account_assignment(
                    InstanceArn=self.instance_arn,
                    TargetId=os.environ['AWS_ACCOUNT_ID'],
                    TargetType='AWS_ACCOUNT',
                    PermissionSetArn=permission_set_arn,
                    PrincipalType='USER',
                    PrincipalId=user['UserId']
                )

                # Wait for assignment to complete
                status_response = self.sso_admin.describe_account_assignment_creation_status(
                    InstanceArn=self.instance_arn,
                    AccountAssignmentCreationRequestId=assignment_response['AccountAssignmentCreationStatus'][
                        'RequestId']
                )
                while status_response['AccountAssignmentCreationStatus']['Status'] == 'IN_PROGRESS':
                    time.sleep(2)
                    status_response = self.sso_admin.describe_account_assignment_creation_status(
                        InstanceArn=self.instance_arn,
                        AccountAssignmentCreationRequestId=assignment_response['AccountAssignmentCreationStatus'][
                            'RequestId']
                    )

                if status_response['AccountAssignmentCreationStatus']['Status'] != 'SUCCEEDED':
                    raise Exception(
                        f"Assignment failed: {status_response['AccountAssignmentCreationStatus'].get('FailureReason')}")

            except self.sso_admin.exceptions.ConflictException:
                print_progress("User already has this permission set assigned", "ℹ️")

            print_progress(f"Permission set created and attached successfully", "✅")
            print(f"   ├─ Name: {permission_set_name}")
            print(f"   ├─ User: {user_email}")
            print(f"   └─ Duration: {session_duration}")

            # Get current permission set details for notification
            permission_set_details = self.sso_admin.describe_permission_set(
                InstanceArn=self.instance_arn,
                PermissionSetArn=permission_set_arn
            )['PermissionSet']

            # Send notification
            self.notifications.send_access_granted(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                account_alias=get_account_alias(self.session) or os.environ['AWS_ACCOUNT_ID'],
                permission_set=permission_set_name,
                permission_set_details=permission_set_details,
                duration_seconds=self.parse_iso8601_duration(session_duration),
                user_email=user_email
            )

            return permission_set_arn

        except Exception as e:
            self._handle_error("Failed to create and attach permission set", e)
            return None

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
                elif unit == 'S':
                    return value
            return 3600  # Default 1 hour
        except Exception:
            return 3600

    def validate_duration(self, requested_duration: str, max_duration: str) -> str:
        """Validate that requested duration doesn't exceed maximum duration."""
        try:
            requested_seconds = self.parse_iso8601_duration(requested_duration)
            max_seconds = self.parse_iso8601_duration(max_duration)
            if requested_seconds > max_seconds:
                print_progress(
                    f"Requested duration exceeds maximum allowed duration of {max_duration}. Using maximum duration.",
                    "⚠️")
                return max_duration

            return requested_duration
        except Exception as e:
            print_progress(f"Invalid duration format. Using default duration of {max_duration}", "⚠️")
            return max_duration

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email in either IAM Identity Center or IAM."""
        try:
            print_progress(f"Looking up user: {email}", "👤")

            # First try IAM Identity Center if we have SSO configured
            if hasattr(self, 'identity_store_id'):
                try:
                    response = self.identitystore.list_users(
                        IdentityStoreId=self.identity_store_id,
                        Filters=[{
                            'AttributePath': 'UserName',
                            'AttributeValue': email
                        }]
                    )
                    users = response.get('Users', [])
                    if users:
                        print_progress(f"Found user in Identity Center: {users[0].get('UserName')}", "✅")
                        return users[0]
                except Exception as e:
                    logger.debug(f"Identity Center lookup failed: {e}")

            # If not found in Identity Center or if SSO is not configured, try IAM
            try:
                paginator = self.iam_client.get_paginator('list_users')
                for page in paginator.paginate():
                    for user in page['Users']:
                        if user['UserName'].lower() == email.lower():
                            print_progress(f"Found user in IAM: {user['UserName']}", "✅")
                            return user

                        try:
                            tags_response = self.iam_client.list_user_tags(UserName=user['UserName'])
                            for tag in tags_response['Tags']:
                                if tag['Key'].lower() == 'email' and tag['Value'].lower() == email.lower():
                                    print_progress(f"Found user in IAM by email tag: {user['UserName']}", "✅")
                                    return user
                        except Exception as e:
                            logger.debug(f"Failed to get tags for user {user['UserName']}: {e}")
                            continue

            except Exception as e:
                logger.error(f"IAM user lookup failed: {e}")

            print_progress(f"No user found with email: {email}", "❌")
            return None

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

    def grant_access(self, user_email: str, permission_set_name: str, requested_duration: str, max_duration: str):
        """Grant access for a user by email and permission set name."""
        try:
            print_progress(f"Granting access for {user_email} with permission set {permission_set_name}...", "🔄")

            # Validate duration
            validated_duration = self.validate_duration(requested_duration, max_duration)
            duration_seconds = self.parse_iso8601_duration(validated_duration)
            duration_display = format_duration(duration_seconds)

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
            print(f"   └─ Duration: {duration_display}")

            # Send notifications using the notification manager
            self.notifications.send_access_granted(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                account_alias=account_alias,
                permission_set=permission_set_name,
                permission_set_details=permission_set_details,
                duration_seconds=duration_seconds,
                user_email=user_email
            )

            if os.environ.get('REVOKATION_WEBHOOK_URL'):
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

    def grant_s3_access(self, user_email: str, bucket_name: str, policy_template: str, duration: str):
        """Grant S3 access to the user by updating the bucket policy."""
        try:
            print_progress(f"Granting S3 access for {user_email} to bucket {bucket_name}...", "🔄")

            # Parse duration and get formatted display
            duration_seconds = self.parse_iso8601_duration(duration)
            duration_display = format_duration(duration_seconds)

            # Find user by email
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Validate that the bucket exists
            s3 = self.session.client('s3')
            try:
                s3.head_bucket(Bucket=bucket_name)
            except s3.exceptions.NoSuchBucket:
                raise ValueError(f"S3 bucket {bucket_name} does not exist")

            # Update bucket policy
            success = self.update_bucket_policy(
                bucket_name=bucket_name,
                user_arn=user['Arn'],
                grant_access=True
            )
            if not success:
                raise ValueError("Failed to update bucket policy")

            # Schedule revocation webhook
            self._schedule_revocation_webhook(
                user_email=user_email,
                duration_seconds=duration_seconds,
                account_id=os.environ['AWS_ACCOUNT_ID'],
                buckets=[bucket_name],
                policy_details={
                    "name": bucket_name,
                    "type": "s3",
                    "template": policy_template,
                }
            )

            # Print success message
            print_progress(f"S3 access granted successfully!", "✅")
            print(f"   ├─ User: {user_email}")
            print(f"   ├─ Bucket: {bucket_name}")
            print(f"   └─ Duration: {duration_display}")

            # Send notifications
            self.notifications.send_s3_access_granted(
                account_id=os.environ['AWS_ACCOUNT_ID'],
                user_email=user_email,
                policy_template=policy_template,
                duration_seconds=duration_seconds,
                bucket_name=bucket_name
            )

        except Exception as e:
            self._handle_error("Failed to grant S3 access", e)

    def _schedule_revocation_webhook(self,
                                     user_email: str,
                                     duration_seconds: int,
                                     account_id: str,
                                     permission_set: Optional[str] = None,
                                     policy_details: Optional[Dict[str, Any]] = None,
                                     buckets: Optional[list] = None):
        """Schedule the revocation webhook after the TTL expires."""

        def send_webhook():
            if not os.environ.get('REVOKATION_WEBHOOK_URL'):
                print("No revocation webhook URL configured, skipping webhook...")
                return

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

        webhook_thread = threading.Thread(target=send_webhook)
        webhook_thread.daemon = True
        webhook_thread.start()

    def revoke_access(self, user_email: str, permission_set_name: str):
        """Revoke access for a user by email and permission set name."""
        try:
            print_progress(f"Revoking access for {user_email} with permission set {permission_set_name}...", "🔄")

            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

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

    def revoke_s3_access(self, user_email: str, bucket_name: str):
        """Revoke S3 access from the user by updating the bucket policy."""
        try:
            print_progress(f"Revoking S3 access for {user_email} from bucket {bucket_name}...", "🔄")

            # Find user by email
            user = self.get_user_by_email(user_email)
            if not user:
                raise ValueError(f"User not found: {user_email}")

            # Update bucket policy
            success = self.update_bucket_policy(
                bucket_name=bucket_name,
                user_arn=user['Arn'],
                grant_access=False
            )
            if not success:
                raise ValueError("Failed to update bucket policy")

            print_progress(f"S3 access revoked successfully for {user_email}", "✅")

            # Notify user
            self.notifications.send_s3_access_revoked(
                user_email=user_email,
                bucket_name=bucket_name
            )

        except Exception as e:
            self._handle_error("Failed to revoke S3 access", e)

    def update_bucket_policy(self, bucket_name: str, user_arn: str, grant_access: bool) -> bool:
        """Update the bucket policy to grant or revoke access to a user."""
        try:
            s3 = self.session.client('s3')

            # Get current bucket policy
            try:
                policy_response = s3.get_bucket_policy(Bucket=bucket_name)
                policy = json.loads(policy_response['Policy'])
            except s3.exceptions.NoSuchBucketPolicy:
                # No existing policy, start with a new one
                policy = {
                    "Version": "2012-10-17",
                    "Statement": []
                }

            # Define the statement ID to identify our policy
            statement_id = f"JITAccess_{user_arn.split('/')[-1]}_{bucket_name}"

            if grant_access:
                # Add a statement to grant access
                statement = {
                    "Sid": statement_id,
                    "Effect": "Allow",
                    "Principal": {"AWS": user_arn},
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
                # Remove any existing statement with the same Sid
                policy['Statement'] = [stmt for stmt in policy['Statement'] if stmt.get('Sid') != statement_id]
                policy['Statement'].append(statement)
            else:
                # Remove the statement that grants access
                policy['Statement'] = [stmt for stmt in policy['Statement'] if stmt.get('Sid') != statement_id]

            # Update the bucket policy
            s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
            return True

        except Exception as e:
            logger.error(f"Failed to update bucket policy for bucket {bucket_name}: {e}")
            return False


def main():
    """Main function to handle command line arguments and execute actions."""
    parser = argparse.ArgumentParser(description='AWS Access Handler')
    parser.add_argument('action', choices=['grant', 'revoke'], help='Action to perform')
    parser.add_argument('--user-email', required=True, help='Email of the user')
    parser.add_argument('--duration', default='PT1H', help='Duration for access (ISO8601 format, e.g., PT1H)')
    parser.add_argument('--bucket-name', required=False, help='Name of the S3 bucket')

    args = parser.parse_args()

    print_progress("Starting AWS Access Handler...", "🚀")

    try:
        handler = AWSAccessHandler()

        if args.action == 'grant':
            # Handle SSO access
            s3_policy = os.environ.get('S3_POLICY')
            s3_managed_policies = os.environ.get('S3_MANAGED_POLICIES').split(',')
            permission_set_name = os.environ.get('PERMISSION_SET_NAME', 'DefaultPermissionSet')
            actions: List[str] = []
            if s3_policy == "ReadOnly":
                actions.append("s3:GetObject")
                actions.append("s3:ListBucket")
            elif s3_policy == "FullAccess":
                actions.append("s3:*")

            inline_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [actions],
                        "resource": [
                            f"arn:aws:s3:::{args.bucket_name}",
                            f"arn:aws:s3:::{args.bucket_name}/*"
                        ]
                    }
                ]
            }

            handler.grant_permission_set(user_email=args.user_email,
                                         permission_set_name=permission_set_name,
                                         session_duration=args.duraion,
                                         inline_policy=inline_policy,
                                         managed_policies=s3_managed_policies)
        else:  # revoke
            # Handle SSO access revocation
            handler.revoke_permission_set(
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
