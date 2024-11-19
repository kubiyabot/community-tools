import boto3
import logging
import os
from typing import Optional, Dict, Any

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class AWSAccessHandler:
    def __init__(self, profile_name: Optional[str] = None):
        """Initialize AWS access handler."""
        self.session = boto3.Session(profile_name=profile_name)
        self.identitystore = self.session.client('identitystore')
        self.sso_admin = self.session.client('sso-admin')
        
        # Get Identity Store ID from SSO Instance
        instances = self.sso_admin.list_instances()['Instances']
        if not instances:
            raise ValueError("No SSO instance found")
        self.instance_arn = instances[0]['InstanceArn']
        self.identity_store_id = instances[0]['IdentityStoreId']

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user in IAM Identity Center by email."""
        try:
            response = self.identitystore.list_users(
                IdentityStoreId=self.identity_store_id,
                Filters=[{
                    'AttributePath': 'UserName',
                    'AttributeValue': email
                }]
            )

            users = response.get('Users', [])
            if not users:
                logger.error(f"No user found with email: {email}")
                return None

            user = users[0]
            logger.info(f"Found existing user: {user['UserName']}")
            return user

        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            raise

    def assign_permission_set(self, user_id: str, permission_set_name: str, account_id: str) -> None:
        """Assign permission set to user."""
        try:
            # Find permission set
            permission_sets = self.sso_admin.list_permission_sets(
                InstanceArn=self.instance_arn
            )['PermissionSets']
            
            target_ps_arn = None
            for ps_arn in permission_sets:
                ps = self.sso_admin.describe_permission_set(
                    InstanceArn=self.instance_arn,
                    PermissionSetArn=ps_arn
                )['PermissionSet']
                
                if ps['Name'] == permission_set_name:
                    target_ps_arn = ps_arn
                    break
            
            if not target_ps_arn:
                raise ValueError(f"Permission set {permission_set_name} not found")

            # Create assignment
            self.sso_admin.create_account_assignment(
                InstanceArn=self.instance_arn,
                TargetId=account_id,
                TargetType='AWS_ACCOUNT',
                PermissionSetArn=target_ps_arn,
                PrincipalType='USER',
                PrincipalId=user_id
            )
            
            logger.info(
                f"Assigned permission set {permission_set_name} "
                f"to user {user_id} in account {account_id}"
            )

        except Exception as e:
            logger.error(f"Error assigning permission set: {str(e)}")
            raise

def main():
    """Main execution function."""
    try:
        # Get environment variables
        user_email = os.environ['KUBIYA_USER_EMAIL']
        account_id = os.environ['AWS_ACCOUNT_ID']
        permission_set = os.environ['PERMISSION_SET_NAME']
        aws_profile = os.environ.get('AWS_PROFILE')

        handler = AWSAccessHandler(aws_profile)
        
        # Find user by email
        user = handler.get_user_by_email(user_email)
        if not user:
            raise ValueError(f"User not found in IAM Identity Center: {user_email}")

        # Assign permission set
        handler.assign_permission_set(
            user_id=user['UserId'],
            permission_set_name=permission_set,
            account_id=account_id
        )

        print({
            "status": "success",
            "user_id": user['UserId'],
            "user_name": user['UserName'],
            "account_id": account_id,
            "permission_set": permission_set
        })

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print({"status": "error", "message": str(e)})
        raise

if __name__ == "__main__":
    main() 