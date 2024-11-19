import logging
import os
import sys
import json
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError, ProfileNotFound
except ImportError as e:
    logger.error(f"Failed to import boto3: {str(e)}")
    print(json.dumps({
        "status": "error",
        "error_type": "ImportError",
        "message": "Required package boto3 is not installed, could not import - this is OK if you're running a discovery process of a source on the kubiya platform"
    }))
    pass

def convert_duration_to_iso8601(duration: str) -> str:
    """Convert duration string (e.g., '1h', '30m') to ISO8601 duration format."""
    try:
        if duration.endswith('h'):
            hours = int(duration[:-1])
            return f"PT{hours}H"
        elif duration.endswith('m'):
            minutes = int(duration[:-1])
            return f"PT{minutes}M"
        else:
            raise ValueError("Duration must end with 'h' for hours or 'm' for minutes")
    except (ValueError, AttributeError) as e:
        error_msg = f"Invalid duration format. Use '1h' for 1 hour, '30m' for 30 minutes. Error: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "error_type": "ValidationError",
            "message": error_msg
        }))
        sys.exit(1)

class AWSAccessHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize AWS access handler."""
        try:
            self.session = boto3.Session(profile_name=profile_name)
            self.identitystore = self.session.client('identitystore')
            self.sso_admin = self.session.client('sso-admin')
            
            # Get Identity Store ID from SSO Instance
            instances = self.sso_admin.list_instances()['Instances']
            if not instances:
                raise ValueError("No SSO instance found - AWS IAM Identity Center must be configured")
            self.instance_arn = instances[0]['InstanceArn']
            self.identity_store_id = instances[0]['IdentityStoreId']
            
        except ProfileNotFound:
            error_msg = f"AWS profile '{profile_name}' not found. Please check your AWS credentials"
            logger.error(error_msg)
            print(json.dumps({
                "status": "error",
                "error_type": "ProfileNotFound",
                "message": error_msg
            }))
            sys.exit(1)
        except ClientError as e:
            error_msg = f"AWS API error: {str(e)}"
            logger.error(error_msg)
            print(json.dumps({
                "status": "error",
                "error_type": "AWSError",
                "message": error_msg,
                "details": e.response['Error']
            }))
            sys.exit(1)
        except Exception as e:
            error_msg = f"Failed to initialize AWS handler: {str(e)}"
            logger.error(error_msg)
            print(json.dumps({
                "status": "error",
                "error_type": "InitializationError",
                "message": error_msg
            }))
            sys.exit(1)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user in IAM Identity Center by email."""
        try:
            response = self.identitystore.list_users(
                IdentityStoreId=self.identity_store_id,
                Filters=[{
                    'AttributePath': 'Emails.Value',
                    'AttributeValue': email
                }]
            )

            users = response.get('Users', [])
            if not users:
                logger.error(f"No user found with email: {email}")
                return None

            user = users[0]
            logger.info(f"Found user: {user['UserName']} (ID: {user['UserId']})")
            return user

        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            raise

    def get_permission_set_details(self, permission_set_name: str) -> Optional[Dict[str, Any]]:
        """Get permission set ARN and details."""
        try:
            permission_sets = self.sso_admin.list_permission_sets(
                InstanceArn=self.instance_arn
            )['PermissionSets']
            
            for ps_arn in permission_sets:
                ps = self.sso_admin.describe_permission_set(
                    InstanceArn=self.instance_arn,
                    PermissionSetArn=ps_arn
                )['PermissionSet']
                
                if ps['Name'] == permission_set_name:
                    logger.info(f"Found permission set: {ps['Name']} (ARN: {ps_arn})")
                    return {
                        'arn': ps_arn,
                        'name': ps['Name'],
                        'description': ps.get('Description', '')
                    }
            
            logger.error(f"Permission set not found: {permission_set_name}")
            return None

        except Exception as e:
            logger.error(f"Error getting permission set details: {str(e)}")
            raise

    def assign_permission_set(self, user_id: str, permission_set_name: str, account_id: str, session_duration: str) -> Dict[str, Any]:
        """Assign permission set to user and return assignment details."""
        try:
            # Get permission set details
            ps_details = self.get_permission_set_details(permission_set_name)
            if not ps_details:
                raise ValueError(f"Permission set {permission_set_name} not found")

            # Convert duration to ISO8601
            iso_duration = convert_duration_to_iso8601(session_duration)
            logger.info(f"Setting session duration to: {iso_duration}")

            # Update permission set with new duration
            self.sso_admin.update_permission_set(
                InstanceArn=self.instance_arn,
                PermissionSetArn=ps_details['arn'],
                SessionDuration=iso_duration
            )

            # Create assignment
            response = self.sso_admin.create_account_assignment(
                InstanceArn=self.instance_arn,
                TargetId=account_id,
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=ps_details['arn'],
                PrincipalType='USER',
                PrincipalId=user_id
            )
            
            assignment_status = response['AccountAssignmentCreationStatus']
            logger.info(
                f"Assigned permission set {permission_set_name} "
                f"to user {user_id} in account {account_id} "
                f"with session duration {session_duration}"
            )

            ps_details['session_duration'] = session_duration
            return {
                'status': assignment_status['Status'],
                'request_id': assignment_status['RequestId'],
                'permission_set': ps_details
            }

        except Exception as e:
            logger.error(f"Error assigning permission set: {str(e)}")
            raise

def main():
    """Main execution function."""
    try:
        # Validate required environment variables
        required_vars = ['KUBIYA_USER_EMAIL', 'AWS_ACCOUNT_ID', 'PERMISSION_SET_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Get environment variables
        user_email = os.environ['KUBIYA_USER_EMAIL']
        account_id = os.environ['AWS_ACCOUNT_ID']
        permission_set = os.environ['PERMISSION_SET_NAME']
        session_duration = os.environ.get('SESSION_DURATION', '1h')
        aws_profile = os.environ.get('AWS_PROFILE')

        handler = AWSAccessHandler(aws_profile)
        
        # Find user by email
        user = handler.get_user_by_email(user_email)
        if not user:
            error_msg = f"User not found in IAM Identity Center: {user_email}"
            print(json.dumps({
                "status": "error",
                "error_type": "UserNotFound",
                "message": error_msg
            }))
            sys.exit(1)

        # Assign permission set and get details
        assignment = handler.assign_permission_set(
            user_id=user['UserId'],
            permission_set_name=permission_set,
            account_id=account_id,
            session_duration=session_duration
        )

        # Return detailed success response
        print(json.dumps({
            "status": "success",
            "user": {
                "id": user['UserId'],
                "name": user['UserName'],
                "email": user_email
            },
            "account_id": account_id,
            "permission_set": assignment['permission_set'],
            "assignment": {
                "status": assignment['status'],
                "request_id": assignment['request_id'],
                "session_duration": session_duration
            },
            "instance_arn": handler.instance_arn
        }, indent=2))
        sys.exit(0)

    except ValueError as e:
        error_msg = str(e)
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "error_type": "ValidationError",
            "message": error_msg
        }))
        sys.exit(1)
    except ClientError as e:
        error_msg = f"AWS API error: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "error_type": "AWSError",
            "message": error_msg,
            "details": e.response['Error']
        }))
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "error_type": "UnexpectedError",
            "message": error_msg
        }))
        sys.exit(1)

if __name__ == "__main__":
    main() 