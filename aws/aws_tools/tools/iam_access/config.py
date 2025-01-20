def try_import(module_name, install_hint=None):
    try:
        return __import__(module_name)
    except ImportError:
        print(f"⚠️  Import Warning: Could not import '{module_name}'.")
        if install_hint:
            print(f"   Hint: You can install it with: {install_hint}")
        else:
            print("   Please ensure the module is properly installed.")

# Import modules with friendly error messages
yaml = try_import("yaml", "pip install pyyaml")
requests = try_import("requests", "pip install requests")
typing = try_import("typing")  # Built-in module, no install hint needed
os = try_import("os")          # Built-in module, no install hint needed

# Additional imports with specific handling
try:
    from typing import Dict, Any, List, Optional
except ImportError:
    print("⚠️  Import Warning: 'typing' module could not be imported.")
    print("   This might indicate an issue with the Python installation.")

try:
    import boto3
except ImportError:
    print("⚠️  Import Warning: 'boto3' module not found.")
    print("   Please ensure Boto3 is installed: pip install boto3")

try:
    from dataclasses import dataclass
except ImportError:
    print("⚠️  Import Warning: 'dataclasses' module could not be imported.")
    print("   Ensure your Python version supports dataclasses (Python 3.7+).")

@dataclass
class PolicyConfig:
    policy_name: str
    aws_account_id: str
    request_name: str

class IAMAccessConfig:
    def __init__(self):
        self.policies: List[PolicyConfig] = []
        self._load_config()
        self._validate_config()

    def _load_config(self):
        """Load configuration from URL specified in environment variable."""
        config_url = os.getenv('AWS_IAM_CONFIG_URL')
        if not config_url:
            raise ValueError("AWS_IAM_CONFIG_URL environment variable not set")

        try:
            response = requests.get(config_url)
            response.raise_for_status()
            config = yaml.safe_load(response.text)
            
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
        session = boto3.Session()
        available_profiles = session.available_profiles

        for policy in self.policies:
            # Validate account access
            for profile in available_profiles:
                try:
                    sts = boto3.Session(profile_name=profile).client('sts')
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