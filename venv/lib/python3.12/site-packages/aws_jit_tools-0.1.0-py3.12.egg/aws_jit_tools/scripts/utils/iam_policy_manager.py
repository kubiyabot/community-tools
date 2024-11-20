import logging
import json
import time
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IAMPolicyManager:
    def __init__(self, session):
        self.iam = session.client('iam')
        self.sts = session.client('sts')
        
    def _generate_policy_name(self, user_id: str, purpose: str) -> str:
        """Generate a deterministic policy name based on context."""
        # Get context from environment variables
        account_id = os.environ.get('AWS_ACCOUNT_ID', '')
        
        # For S3 access, use buckets and policy template
        if os.environ.get('BUCKETS') and os.environ.get('POLICY_TEMPLATE'):
            buckets = os.environ.get('BUCKETS', '').replace(',', '_')
            policy_template = os.environ.get('POLICY_TEMPLATE', '')
            policy_name = f"jit_s3_policy_{account_id}_{policy_template}_{buckets}_{user_id}"
        else:
            # For SSO access, use permission set
            permission_set = os.environ.get('PERMISSION_SET_NAME', '')
            policy_name = f"jit_policy_{purpose}_{account_id}_{permission_set}_{user_id}"
        
        # Remove any invalid characters and ensure uniqueness
        policy_name = policy_name.replace('@', '_at_').replace('.', '_dot_')
        return policy_name[:128]  # AWS has a length limit for policy names

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
            
            # Check if policy already exists
            try:
                existing_policy = self.iam.get_policy(PolicyArn=f"arn:aws:iam::{self._get_account_id()}:policy/{policy_name}")
                logger.info(f"Policy already exists: {policy_name}")
                return existing_policy['Policy']['Arn']
            except self.iam.exceptions.NoSuchEntityException:
                # For S3 access, we don't create new policies - they should exist
                if os.environ.get('BUCKETS') and os.environ.get('POLICY_TEMPLATE'):
                    logger.error("S3 access policy not found - should be pre-created")
                    return None
                
                # For SSO access, create new policy
                response = self.iam.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document),
                    Description=f"Kubiya JIT access policy for {purpose} - Account: {os.environ.get('AWS_ACCOUNT_ID')} - Permission Set: {os.environ.get('PERMISSION_SET_NAME')}"
                )
                
                logger.info(f"Created policy: {policy_name}")
                return response['Policy']['Arn']
            
        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            return None

    def cleanup_user_policies(self, user_name: str) -> bool:
        """Clean up JIT policies for a user based on current context."""
        try:
            # Get context from environment variables
            account_id = os.environ.get('AWS_ACCOUNT_ID', '')
            
            # Determine policy pattern based on context
            if os.environ.get('BUCKETS') and os.environ.get('POLICY_TEMPLATE'):
                # S3 access case
                buckets = os.environ.get('BUCKETS', '').replace(',', '_')
                policy_template = os.environ.get('POLICY_TEMPLATE', '')
                policy_pattern = f"jit_s3_policy_{account_id}_{policy_template}_{buckets}_{user_name}"
            else:
                # SSO access case
                permission_set = os.environ.get('PERMISSION_SET_NAME', '')
                if not permission_set:
                    logger.error("Missing required environment variables for policy cleanup")
                    return False
                policy_pattern = f"jit_policy_{account_id}_{permission_set}_{user_name}"

            policy_pattern = policy_pattern.replace('@', '_at_').replace('.', '_dot_')

            # List attached policies
            response = self.iam.list_attached_user_policies(
                UserName=user_name
            )
            
            success = True
            for policy in response['AttachedPolicies']:
                # Only cleanup policies matching our context
                if policy_pattern in policy['PolicyName']:
                    logger.info(f"Found matching policy to cleanup: {policy['PolicyName']}")
                    # For S3 access, only detach the policy (don't delete pre-created policies)
                    if os.environ.get('BUCKETS') and os.environ.get('POLICY_TEMPLATE'):
                        if not self.detach_user_policy(user_name, policy['PolicyArn']):
                            success = False
                    else:
                        # For SSO access, detach and delete the policy
                        if self.detach_user_policy(user_name, policy['PolicyArn']):
                            if not self.delete_policy(policy['PolicyArn']):
                                success = False
                        else:
                            success = False
                        
            return success
            
        except Exception as e:
            logger.error(f"Failed to cleanup user policies: {e}")
            return False

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
            # AWS requires some time after detaching before deletion
            time.sleep(2)
            
            self.iam.delete_policy(
                PolicyArn=policy_arn
            )
            logger.info(f"Deleted policy {policy_arn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            return False

    def get_user_policies(self, user_name: str) -> List[str]:
        """Get JIT policy ARNs attached to a user for current context."""
        try:
            # Get context from environment variables
            account_id = os.environ.get('AWS_ACCOUNT_ID', '')
            permission_set = os.environ.get('PERMISSION_SET_NAME', '')
            
            if not account_id or not permission_set:
                logger.error("Missing required environment variables for getting user policies")
                return []

            # Generate the policy name pattern to match
            policy_pattern = f"jit_policy_{account_id}_{permission_set}_{user_name}"
            policy_pattern = policy_pattern.replace('@', '_at_').replace('.', '_dot_')

            response = self.iam.list_attached_user_policies(
                UserName=user_name
            )
            
            return [
                policy['PolicyArn'] 
                for policy in response['AttachedPolicies']
                if policy_pattern in policy['PolicyName']
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user policies: {e}")
            return [] 