from typing import Optional
from botocore.exceptions import ClientError
import logging

try:
    import boto3
except ImportError:
    print("boto3 not installed, skipping import (might be a discovery call)")
    pass

logger = logging.getLogger(__name__)

def get_account_alias(session: boto3.Session) -> Optional[str]:
    """Get AWS account alias if it exists."""
    try:
        iam = session.client('iam')
        response = iam.list_account_aliases()
        aliases = response.get('AccountAliases', [])
        return aliases[0] if aliases else None
    except Exception as e:
        logger.warning(f"Could not get account alias: {e}")
        return None

def get_permission_set_details(session: boto3.Session, instance_arn: str, permission_set_arn: str) -> Optional[dict]:
    """Get detailed information about a permission set."""
    try:
        sso_admin = session.client('sso-admin')
        response = sso_admin.describe_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        return response.get('PermissionSet')
    except Exception as e:
        logger.warning(f"Could not get permission set details: {e}")
        return None 