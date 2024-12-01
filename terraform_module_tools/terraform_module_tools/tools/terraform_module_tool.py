from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pathlib import Path
from ..parser import TerraformModuleParser

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_LENGTH = 1024

def map_terraform_type_to_arg_type(tf_type: str) -> str:
    """Map Terraform types to Kubiya SDK Arg types."""
    # Only use supported types: "str", "bool", "int"
    base_type = tf_type.split('(')[0].lower()
    
    if base_type == 'bool':
        return 'bool'
    elif base_type == 'number':
        return 'int'  # Map all numbers to int
    
    # Everything else (string, list, map, object) becomes str
    return 'str'

def truncate_description(description: str) -> str:
    """Truncate description to max length."""
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return description[:MAX_DESCRIPTION_LENGTH-3] + "..."
    return description

def generate_example(var_name: str, tf_type: str) -> Any:
    """Generate example value based on variable name and type."""
    base_type = tf_type.split('(')[0].lower()
    
    if base_type == 'bool':
        return True
    elif base_type == 'number':
        return 42
    elif base_type in ['list', 'set']:
        return '["value1", "value2"]'  # JSON string for arrays
    elif base_type == 'map':
        return '{"key": "value"}'  # JSON string for maps
    elif base_type == 'object':
        return '{"field": "value"}'  # JSON string for objects
    
    # Common patterns for string values
    if 'name' in var_name:
        return "example-name"
    elif 'cidr' in var_name:
        return "10.0.0.0/16"
    elif 'region' in var_name:
        return "us-west-2"
    
    return "example-value"

def get_default_value(var_config: Dict[str, Any], arg_type: str) -> Any:
    """Convert default value to correct type."""
    if 'default' not in var_config:
        return None
        
    default = var_config['default']
    
    if arg_type == 'str':
        if isinstance(default, (dict, list)):
            return json.dumps(default)  # Convert complex types to JSON string
        return str(default)
    elif arg_type == 'int':
        try:
            return int(float(default))  # Handle both int and float defaults
        except (ValueError, TypeError):
            return None
    elif arg_type == 'bool':
        return bool(default)
    
    return None

class TerraformModuleTool(Tool):
    """Base class for Terraform module tools."""
    def __init__(
        self,
        name: str,
        description: str,
        module_config: Dict[str, Any],
        action: str = 'plan',
        with_pr: bool = False,
        env: List[str] = None,
        secrets: List[str] = None,
    ):
        # Auto-discover variables
        try:
            parser = TerraformModuleParser(
                source_url=module_config['source']['location'],
                ref=module_config['source'].get('version'),
                subfolder=module_config['source'].get('path')
            )
            variables, warnings, errors = parser.get_variables()
            
            for warning in warnings:
                logger.warning(f"Variable discovery warning: {warning}")
            for error in errors:
                logger.error(f"Variable discovery error: {error}")
            
        except Exception as e:
            logger.error(f"Failed to auto-discover variables: {str(e)}")
            variables = {}

        # Prepare script content
        script_name = 'plan_with_pr.py' if action == 'plan' and with_pr else f'{action}.py'
        pre_script = module_config.get('pre_script', '')
        if pre_script:
            pre_script = f"\n# Run pre-script\ncat > /tmp/pre_script.sh << 'EOF'\n{pre_script}\nEOF\nchmod +x /tmp/pre_script.sh\n/tmp/pre_script.sh || exit 1\n"

        content = f"""
# Install required packages
pip install -q slack_sdk requests

# Download hcl2json if needed
if ! command -v hcl2json &> /dev/null; then
    curl -L -o /usr/local/bin/hcl2json https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64
    chmod +x /usr/local/bin/hcl2json
fi
{pre_script}
# Run Terraform {action}
python /opt/scripts/{script_name} '{{{{ .module_config | toJson }}}}' '{{{{ .variables | toJson }}}}' || exit 1
"""

        # Convert variables to args
        args = []
        for var_name, var_config in variables.items():
            # Map to supported type
            arg_type = map_terraform_type_to_arg_type(var_config['type'])
            
            # Generate example
            example = generate_example(var_name, var_config['type'])
            
            # Get properly typed default
            default = get_default_value(var_config, arg_type)
            
            # Create short description
            description = truncate_description(
                f"{var_config['description']} (Type: {var_config['type']})"
            )
            
            # Add JSON hint for complex types
            if var_config['type'] not in ['string', 'number', 'bool']:
                description = truncate_description(
                    f"{description}\nProvide as JSON string"
                )
            
            args.append(
                Arg(
                    name=var_name,
                    description=description,
                    type=arg_type,
                    required=var_config.get('required', False),
                    default=default
                )
            )

        # Get script files
        script_files = {}
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name.endswith('.py'):
                script_files[script_file.name] = script_file.read_text()

        # Add common environment variables and secrets
        env = (env or []) + [
            "SLACK_CHANNEL_ID",
            "SLACK_THREAD_TS",
            "GIT_TOKEN",
        ]
        
        secrets = (secrets or []) + [
            "SLACK_API_TOKEN",
        ]

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            icon_url="https://user-images.githubusercontent.com/31406378/108641411-f9374f00-7496-11eb-82a7-0fa2a9cc5f93.png",
            args=args,
            env=env,
            secrets=secrets,
            with_files=[
                FileSpec(
                    destination=f"/opt/scripts/{script_name}",
                    content=script_content
                )
                for script_name, script_content in script_files.items()
            ]
        )