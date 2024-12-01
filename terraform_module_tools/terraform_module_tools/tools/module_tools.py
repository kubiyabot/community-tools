from kubiya_sdk.tools.registry import tool_registry
from pathlib import Path
from .terraform_module_tool import TerraformModuleTool
from ..scripts.config_loader import get_module_configs

# Load configurations
try:
    MODULE_CONFIGS = get_module_configs()
except Exception as e:
    print(f"Error loading configurations: {e}")
    MODULE_CONFIGS = {}

def create_terraform_module_tool(config: dict, action: str, with_pr: bool = False):
    """Create a Terraform module tool from configuration."""
    
    # Generate tool name
    action_suffix = f"_{action}"
    if action == 'plan' and with_pr:
        action_suffix = '_plan_pr'
    tool_name = f"tf_{config['name'].lower().replace(' ', '_')}{action_suffix}"
    
    # Create tool description
    action_desc = {
        'plan': 'Plan changes for',
        'plan_pr': 'Plan changes and create PR for',
        'apply': 'Apply changes to'
    }
    description = f"{action_desc.get(action, 'Manage')} {config['description']}"

    return TerraformModuleTool(
        name=tool_name,
        description=description,
        module_config={
            'source': config['source'],
            'version': config['version'],
            'variables': config['variables']
        },
        action=action,
        with_pr=with_pr
    )

# Export necessary components
__all__ = ['create_terraform_module_tool', 'MODULE_CONFIGS'] 