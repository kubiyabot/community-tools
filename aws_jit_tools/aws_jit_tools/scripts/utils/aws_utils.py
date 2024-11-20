from typing import Optional, Union, TYPE_CHECKING
import logging
from dataclasses import dataclass

# Type checking block - these types are only used during static type checking
if TYPE_CHECKING:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
else:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception
    BotoCoreError = Exception

logger = logging.getLogger(__name__)

# Try to import boto3, but don't fail if it's not available
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError as e:
    logger.debug(f"Failed to import boto3/botocore: {str(e)}")
    BOTO3_AVAILABLE = False

def get_account_alias(session: 'Optional[boto3.Session]') -> Optional[str]:
    """Get AWS account alias if it exists.
    
    Args:
        session: boto3 Session object
        
    Returns:
        str: Account alias if found, None otherwise
        
    Raises:
        ClientError: If there is an AWS API error
        NoCredentialsError: If AWS credentials are missing/invalid
    """
    if not session:
        logger.error("Invalid or missing boto3 session")
        return None
        
    try:
        iam = session.client('iam')
        response = iam.list_account_aliases()
        aliases = response.get('AccountAliases', [])
        return aliases[0] if aliases else None
        
    except NoCredentialsError as e:
        logger.error(f"Missing/invalid AWS credentials: {str(e)}")
        raise
    except ClientError as e:
        logger.error(f"AWS API error getting account alias: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting account alias: {str(e)}")
        raise

def get_permission_set_details(
    session: 'Optional[boto3.Session]',
    instance_arn: str,
    permission_set_arn: str
) -> Optional[dict]:
    """Get detailed information about a permission set.
    
    Args:
        session: boto3 Session object
        instance_arn: SSO instance ARN
        permission_set_arn: Permission set ARN
        
    Returns:
        dict: Permission set details if found, None otherwise
        
    Raises:
        ClientError: If there is an AWS API error
        NoCredentialsError: If AWS credentials are missing/invalid
        ValueError: If instance_arn or permission_set_arn are invalid
    """
    if not session:
        logger.error("Invalid or missing boto3 session")
        return None
        
    if not instance_arn or not permission_set_arn:
        logger.error("Missing required ARN parameter(s)")
        raise ValueError("instance_arn and permission_set_arn are required")
        
    try:
        sso_admin = session.client('sso-admin')
        response = sso_admin.describe_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        return response.get('PermissionSet')
        
    except NoCredentialsError as e:
        logger.error(f"Missing/invalid AWS credentials: {str(e)}")
        raise
    except ClientError as e:
        logger.error(f"AWS API error getting permission set details: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting permission set details: {str(e)}")
        raise