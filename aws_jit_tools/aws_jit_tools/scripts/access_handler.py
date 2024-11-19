import logging
import os
import sys
import json
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSOAssignmentHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize AWS clients and get SSO instance information."""
        try:
            self.session = boto3.Session(profile_name=profile_name)
            self.identitystore = self.session.client('identitystore')
            self.sso_admin = self.session.client('sso-admin')
            
            # Get Identity Store ID from SSO Instance
            instances = self.sso_admin.list_instances()['Instances']
            if not instances:
                raise ValueError("No SSO instance found")
            
            self.instance_arn = instances[0]['InstanceArn']
            self.identity_store_id = instances[0]['IdentityStoreId']
            logger.info(f"Found SSO instance ARN: {self.instance_arn}")
            logger.info(f"Found Identity Store ID: {self.identity_store_id}")
            
        except Exception as e:
            self._handle_error("Failed to initialize AWS handler", e)

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
                self._handle_error("User lookup failed", ValueError(f"No user found with email: {email}"))
            
            logger.info(f"Found user ID: {users[0]['UserId']} for email: {email}")
            return users[0]

        except Exception as e:
            self._handle_error("Error finding user by email", e)

    def get_permission_set_arn(self, permission_set_name: str) -> str:
        """Get Permission Set ARN by name."""
        try:
            permission_sets = self.sso_admin.list_permission_sets(
                InstanceArn=self.instance_arn
            )['PermissionSets']
            
            for ps_arn in permission_sets:
                response = self.sso_admin.describe_permission_set(
                    InstanceArn=self.instance_arn,
                    PermissionSetArn=ps_arn
                )
                if response['PermissionSet']['Name'] == permission_set_name:
                    logger.info(f"Found Permission Set ARN: {ps_arn}")
                    return ps_arn
            
            self._handle_error(
                "Permission Set lookup failed", 
                ValueError(f"Permission set not found: {permission_set_name}")
            )

        except Exception as e:
            self._handle_error("Error getting permission set ARN", e)

    def create_assignment(self, account_id: str, permission_set_name: str, user_email: str) -> Dict:
        """Create the SSO assignment."""
        try:
            # Get user details
            user = self.get_user_by_email(user_email)
            
            # Get permission set ARN
            permission_set_arn = self.get_permission_set_arn(permission_set_name)
            
            # Create the assignment
            response = self.sso_admin.create_account_assignment(
                InstanceArn=self.instance_arn,
                TargetId=account_id,
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=permission_set_arn,
                PrincipalType='USER',
                PrincipalId=user['UserId']
            )
            
            # Wait for the assignment to complete
            request_id = response['AccountAssignmentCreationStatus']['RequestId']
            logger.info(f"Assignment request ID: {request_id}")
            
            return {
                "status": "success",
                "message": f"Successfully assigned {permission_set_name} to {user_email} for account {account_id}",
                "details": response['AccountAssignmentCreationStatus']
            }

        except Exception as e:
            self._handle_error("Error creating assignment", e)

    def _handle_error(self, message: str, error: Exception):
        """Handle and log errors."""
        error_msg = f"{message}: {str(error)}"
        logger.error(error_msg)
        print(json.dumps({
            "status": "error",
            "error_type": type(error).__name__,
            "message": error_msg
        }))
        sys.exit(1)

def main():
    """Main execution function."""
    try:
        # Get required environment variables
        required_vars = ['AWS_ACCOUNT_ID', 'PERMISSION_SET_NAME', 'USER_EMAIL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        account_id = os.getenv('AWS_ACCOUNT_ID')
        permission_set_name = os.getenv('PERMISSION_SET_NAME')
        user_email = os.getenv('USER_EMAIL')
        aws_profile = os.getenv('AWS_PROFILE')  # Optional
        
        # Initialize handler
        handler = SSOAssignmentHandler(aws_profile)
        
        # Create assignment
        result = handler.create_assignment(account_id, permission_set_name, user_email)
        
        # Print result
        print(json.dumps(result))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(json.dumps({
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
