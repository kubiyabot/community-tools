import logging
import json
import time
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class IAMPolicyManager:
    def __init__(self, session):
        self.iam = session.client('iam')
        self.sts = session.client('sts')
        
    def _generate_policy_name(self, user_id: str, purpose: str) -> str:
        """Generate a deterministic policy name based on context."""
        account_id = os.environ.get('AWS_ACCOUNT_ID', '')
        if purpose == 's3_access':
            buckets = os.environ.get('BUCKETS', '').replace(',', '_')
            policy_template = os.environ.get('POLICY_TEMPLATE', '')
            policy_name = f"jit_s3_policy_{account_id}_{policy_template}_{buckets}_{user_id}"
        else:
            permission_set = os.environ.get('PERMISSION_SET_NAME', '')
            policy_name = f"jit_policy_{purpose}_{account_id}_{permission_set}_{user_id}"
        policy_name = policy_name.replace('@', '_at_').replace('.', '_dot_')
        return policy_name[:128]

    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        try:
            return self.sts.get_caller_identity()["Account"]
        except Exception as e:
            logger.error(f"Failed to get account ID: {e}")
            raise

    def create_policy(self, policy_document: Dict[str, Any], purpose: str, user_id: str) -> Optional[str]:
        """Create an IAM policy and return its ARN."""
        try:
            policy_name = self._generate_policy_name(user_id, purpose)
            # Create new policy
            response = self.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=f"JIT access policy for {purpose} - Created for {user_id}"
            )
            logger.info(f"Created policy: {policy_name}")
            return response['Policy']['Arn']
        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            return None

    def attach_user_policy(self, user_name: str, policy_arn: str) -> bool:
        """Attach an IAM policy to a user."""
        try:
            self.iam.attach_user_policy(
                UserName=user_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy {policy_arn} to user {user_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to attach policy to user: {e}")
            return False

    def detach_user_policy(self, user_name: str, policy_arn: str) -> bool:
        """Detach an IAM policy from a user."""
        try:
            self.iam.detach_user_policy(
                UserName=user_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Detached policy {policy_arn} from user {user_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to detach policy from user: {e}")
            return False

    def delete_policy(self, policy_arn: str) -> bool:
        """Delete an IAM policy."""
        try:
            time.sleep(2)
            self.iam.delete_policy(
                PolicyArn=policy_arn
            )
            logger.info(f"Deleted policy {policy_arn}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            return False

    def cleanup_user_policies(self, user_name: str) -> bool:
        """Clean up JIT policies for a user based on current context."""
        try:
            policy_name = self._generate_policy_name(user_id=user_name, purpose='s3_access')
            response = self.iam.list_attached_user_policies(
                UserName=user_name
            )
            success = True
            for policy in response['AttachedPolicies']:
                if policy_name in policy['PolicyName']:
                    logger.info(f"Found matching policy to cleanup: {policy['PolicyName']}")
                    if self.detach_user_policy(user_name, policy['PolicyArn']):
                        if not self.delete_policy(policy['PolicyArn']):
                            success = False
                    else:
                        success = False
            return success
        except Exception as e:
            logger.error(f"Failed to cleanup user policies: {e}")
            return False 