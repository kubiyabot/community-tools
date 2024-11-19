import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PermissionSetConfig:
    name: str
    description: str
    aws_managed_policies: list
    inline_policies: Optional[Dict[str, Any]] = None
    session_duration: str = "PT1H"

@dataclass
class AccountConfig:
    id: str
    name: str
    permission_sets: Dict[str, PermissionSetConfig]

class AWSJITConfig:
    def __init__(self):
        self.config_path = self._get_config_path()
        self.accounts = {}
        self._load_config()

    def _get_config_path(self) -> Path:
        """Get path to the config file in repository root."""
        # Start from the current file and go up to find the repo root
        current_dir = Path(__file__).resolve().parent
        while current_dir.name != 'aws_jit_tools' and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        
        config_path = current_dir / 'aws_jit_config.yaml'
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        return config_path

    def _load_config(self):
        """Load and parse configuration from YAML file."""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            self._parse_config(config)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise

    def _parse_config(self, config: Dict[str, Any]):
        """Parse the loaded configuration."""
        for account in config.get('accounts', []):
            permission_sets = {}
            
            for ps in account.get('permission_sets', []):
                permission_sets[ps['name']] = PermissionSetConfig(
                    name=ps['name'],
                    description=ps.get('description', ''),
                    aws_managed_policies=ps.get('aws_managed_policies', []),
                    inline_policies=ps.get('inline_policies'),
                    session_duration=ps.get('session_duration', 'PT1H')
                )

            self.accounts[account['id']] = AccountConfig(
                id=account['id'],
                name=account.get('name', f"Account {account['id']}"),
                permission_sets=permission_sets
            )

    def get_permission_set(self, account_id: str, name: str) -> Optional[PermissionSetConfig]:
        """Get permission set configuration by name."""
        account = self.accounts.get(account_id)
        if not account:
            return None
        return account.permission_sets.get(name)

    def validate_permission_set(self, account_id: str, name: str) -> bool:
        """Validate if a permission set exists."""
        return self.get_permission_set(account_id, name) is not None 