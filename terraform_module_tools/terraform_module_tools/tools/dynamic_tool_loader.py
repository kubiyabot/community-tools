import os
import yaml
from typing import Dict, Any, List
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from ..parser import TerraformModuleParser
from .terraform_module_tool import create_terraform_tool

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'configs')

def _create_arg_from_variable(var_name: str, var_info: Dict[str, Any]) -> Arg:
    """Create a Kubiya tool argument from a Terraform variable."""
    description = var_info.description or f"Variable: {var_name}"
    if var_info.default:
        description += f"\nDefault: {var_info.default}"
    
    return Arg(
        name=var_name,
        description=description,
        required=var_info.required,
        type=var_info.type,
        default=var_info.default if not var_info.required else None,
    )

def load_terraform_tools():
    """Load all Terraform tools from configuration files."""
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(('.yaml', '.yml')):
            config_path = os.path.join(CONFIG_DIR, filename)
            with open(config_path, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    create_tools_from_config(config)
                except Exception as e:
                    print(f"Error loading config {filename}: {str(e)}")

def create_tools_from_config(config: Dict[str, Any]):
    """Create all tools for a module with dynamic variable arguments."""
    module_name = config['name']
    source_config = config['source']
    
    # Parse module variables
    parser = TerraformModuleParser(
        source_url=source_config['location'],
        ref=source_config.get('git_config', {}).get('ref'),
        subfolder=source_config.get('git_config', {}).get('subfolder')
    )
    
    variables = parser.get_variables()
    
    # Create arguments from variables
    variable_args = [
        _create_arg_from_variable(name, var_info)
        for name, var_info in variables.items()
    ]
    
    # Create tools with variable arguments
    for action in ['plan', 'apply']:
        tool = create_terraform_tool(
            name=f"iac_{module_name}_{action}",
            description=f"{action.capitalize()} {config['description']}",
            source_config=source_config,
            variable_args=variable_args,
            action=action,
            env=config.get('env', []),
            secrets=config.get('secrets', [])
        )
        
        tool_registry.register('terraform_modules', tool)
    
    # Create variables tool
    vars_tool = create_terraform_tool(
        name=f"iac_{module_name}_vars",
        description=f"Show variables for {config['description']}",
        source_config=source_config,
        action='vars',
        env=config.get('env', []),
        secrets=config.get('secrets', [])
    )
    
    tool_registry.register('terraform_modules', vars_tool) 