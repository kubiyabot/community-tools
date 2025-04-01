import requests
from typing import List
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class PolicyConfig:
    policy_name: str
    aws_account_id: str
    request_name: str

class IAMAccessConfig:
    def __init__(self):
        self.policies: List[PolicyConfig] = []
        self._yaml = None
        self._boto3 = None
        self._load_config()
        self._validate_config()

    @property
    def yaml(self):
        """Lazy load yaml module only when needed."""
        if self._yaml is None:
            import yaml
            self._yaml = yaml
        return self._yaml

    @property
    def boto3(self):
        """Lazy load boto3 module only when needed."""
        if self._boto3 is None:
            import boto3
            self._boto3 = boto3
        return self._boto3

    def _load_config(self):
        """Load configuration from URL specified in environment variable."""
        config_url = os.getenv('AWS_IAM_CONFIG_URL')
        if not config_url:
            raise ValueError("AWS_IAM_CONFIG_URL environment variable not set")

        try:
            response = requests.get(config_url)
            response.raise_for_status()
            config = self.yaml.safe_load(response.text)
            
            for policy in config.get('policies', []):
                self.policies.append(PolicyConfig(
                    policy_name=policy['policy_name'],
                    aws_account_id=policy['aws_account_id'],
                    request_name=policy['request_name']
                ))
        except Exception as e:
            raise RuntimeError(f"Failed to load IAM configuration: {str(e)}")

    def _validate_config(self):
        """Validate the loaded configuration."""
        if not self.policies:
            raise ValueError("No policies defined in configuration")

        # Validate AWS accounts are accessible
        session = self.boto3.Session()
        available_profiles = session.available_profiles

        for policy in self.policies:
            # Validate account access
            for profile in available_profiles:
                try:
                    sts = self.boto3.Session(profile_name=profile).client('sts')
                    account_id = sts.get_caller_identity()['Account']
                    if account_id == policy.aws_account_id:
                        break
                except Exception:
                    continue
            else:
                raise ValueError(f"AWS account {policy.aws_account_id} not accessible with any available profile")

    def get_policy_by_name(self, request_name: str) -> Optional[PolicyConfig]:
        """Get policy configuration by request name."""
        for policy in self.policies:
            if policy.request_name == request_name:
                return policy
        return None 