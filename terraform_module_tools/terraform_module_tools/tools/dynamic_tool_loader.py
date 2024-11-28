import os
import yaml
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .terraform_module_tool import TerraformModuleTool

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'configs')

def load_terraform_tools():
    # Read all YAML config files from the CONFIG_DIR
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            config_path = os.path.join(CONFIG_DIR, filename)
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                create_tool_from_config(config)

def create_tool_from_config(config):
    name = config.get('name')
    description = config.get('description', '')
    terraform_module = config.get('terraform_module')
    auto_detect_vars = config.get('auto_detect_vars', True)
    
    # Only process variables if auto_detect_vars is False
    args = []
    if not auto_detect_vars:
        for var in config.get('variables', []):
            args.append(Arg(
                name=var['name'],
                description=var.get('description', ''),
                required=var.get('required', False),
                default=var.get('default')
            ))
    
    tool = TerraformModuleTool(
        name=name,
        description=description,
        terraform_module=terraform_module,
        args=args if not auto_detect_vars else None,
        env=config.get('env', []),
        secrets=config.get('secrets', []),
        mermaid=config.get('mermaid', None),
        auto_detect_vars=auto_detect_vars
    )
    tool_registry.register('terraform_modules', tool) 