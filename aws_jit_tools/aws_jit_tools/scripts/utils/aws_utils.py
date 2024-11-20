from typing import Optional, Union
import logging
from dataclasses import dataclass
from functools import wraps

# Initialize logger
logger = logging.getLogger(__name__)

# Try to import boto3, with better error handling
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import boto3/botocore: {str(e)}")
    logger.warning("boto3/botocore not installed, some functionality will be limited")
    BOTO3_AVAILABLE = False
    # Define dummy exception classes for type checking
    class ClientError(Exception): pass
    class NoCredentialsError(Exception): pass
    class BotoCoreError(Exception): pass

@dataclass
class PermissionSet:
    """Data class to represent Permission Set details"""
    name: str
    arn: str
    description: Optional[str] = None
    session_duration: Optional[str] = None
    relay_state: Optional[str] = None

def require_boto3(func):
    """Decorator to check if boto3 is available before executing function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not BOTO3_AVAILABLE:
            logger.error(f"boto3 is required for {func.__name__} but is not available")
            raise ImportError("boto3 is required but not installed")
        return func(*args, **kwargs)
    return wrapper

def validate_session(session: Optional[boto3.Session]) -> bool:
    """Validate boto3 session object"""
    if not BOTO3_AVAILABLE:
        return False
    return bool(session and isinstance(session, boto3.Session))

@require_boto3
def get_account_alias(session: Optional[boto3.Session]) -> Optional[str]:
    """
    Get AWS account alias if it exists.
    
    Args:
        session: boto3 Session object
        
    Returns:
        str: Account alias if found, None otherwise
        
    Raises:
        ImportError: If boto3 is not installed
        ClientError: If there is an AWS API error
        NoCredentialsError: If AWS credentials are missing/invalid
    """
    if not validate_session(session):
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

@require_boto3
def get_permission_set_details(
    session: Optional[boto3.Session],
    instance_arn: str,
    permission_set_arn: str
) -> Optional[PermissionSet]:
    """
    Get detailed information about a permission set.
    
    Args:
        session: boto3 Session object
        instance_arn: SSO instance ARN
        permission_set_arn: Permission set ARN
        
    Returns:
        PermissionSet: Permission set details if found, None otherwise
        
    Raises:
        ImportError: If boto3 is not installed
        ClientError: If there is an AWS API error
        NoCredentialsError: If AWS credentials are missing/invalid
        ValueError: If instance_arn or permission_set_arn are invalid
    """
    if not validate_session(session):
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
        
        permission_set_data = response.get('PermissionSet', {})
        return PermissionSet(
            name=permission_set_data.get('Name', ''),
            arn=permission_set_data.get('PermissionSetArn', ''),
            description=permission_set_data.get('Description'),
            session_duration=permission_set_data.get('SessionDuration'),
            relay_state=permission_set_data.get('RelayState')
        )
        
    except NoCredentialsError as e:
        logger.error(f"Missing/invalid AWS credentials: {str(e)}")
        raise
    except ClientError as e:
        logger.error(f"AWS API error getting permission set details: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting permission set details: {str(e)}")
        raise