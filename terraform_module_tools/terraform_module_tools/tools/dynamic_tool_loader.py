import os
import yaml
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .terraform_module_tool import (
    TerraformGetVarsTool,
    TerraformPlanTool,
    TerraformApplyTool
)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'configs')

def load_terraform_tools():
    """Load all Terraform tools from configuration files"""
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(('.yaml', '.yml')):
            config_path = os.path.join(CONFIG_DIR, filename)
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                create_tools_from_config(config)

def create_tools_from_config(config):
    """Create all tools for a module"""
    module_name = config['name']
    module_url = config['terraform_module']
    env = config.get('env', [])
    secrets = config.get('secrets', [])
    
    # Create get-vars tool
    vars_tool = TerraformGetVarsTool(
        name=f"iac_{module_name}_vars",
        description=f"Get variables for {config['description']}",
        terraform_module=module_url,
        env=env,
        secrets=secrets
    )
    tool_registry.register('terraform_modules', vars_tool)
    
    # Create plan tool
    plan_tool = TerraformPlanTool(
        name=f"iac_{module_name}_plan",
        description=f"Plan {config['description']}",
        terraform_module=module_url,
        env=env,
        secrets=secrets
    )
    tool_registry.register('terraform_modules', plan_tool)
    
    # Create apply tool
    apply_tool = TerraformApplyTool(
        name=f"iac_{module_name}_apply",
        description=f"Apply {config['description']}",
        terraform_module=module_url,
        env=env,
        secrets=secrets
    )
    tool_registry.register('terraform_modules', apply_tool) 