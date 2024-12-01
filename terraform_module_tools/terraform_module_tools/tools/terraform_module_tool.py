from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pathlib import Path
from ..parser import TerraformModuleParser

logger = logging.getLogger(__name__)

def map_terraform_type_to_arg_type(tf_type: str) -> str:
    """Map Terraform types to Kubiya SDK Arg types."""
    # Extract base type and nested type if present
    base_type = tf_type.split('(')[0].lower()
    nested_type = None
    if '(' in tf_type and ')' in tf_type:
        nested_type = tf_type[tf_type.index('(')+1:tf_type.rindex(')')].lower()

    # Map to valid Arg types: "str", "array", "bool", "int", "float"
    if base_type == 'bool':
        return 'bool'
    elif base_type == 'number':
        if '.' in str(base_type) or nested_type == 'float':
            return 'float'
        return 'int'
    elif base_type in ['list', 'set']:
        return 'array'
    elif base_type == 'string':
        return 'str'
    
    # All complex types (map, object) default to str (will be passed as JSON)
    return 'str'

def generate_example(var_name: str, tf_type: str) -> Any:
    """Generate example value based on variable name and type."""
    base_type = tf_type.split('(')[0].lower()
    
    # Common patterns in variable names
    if 'name' in var_name:
        return "example-name"
    elif 'cidr' in var_name:
        return "10.0.0.0/16"
    elif 'region' in var_name:
        return "us-west-2"
    elif 'enabled' in var_name or base_type == 'bool':
        return True
    elif base_type == 'number':
        if '.' in str(base_type):
            return 42.0
        return 42
    elif base_type in ['list', 'set']:
        return ["value1", "value2"]
    elif base_type == 'map':
        return json.dumps({"key1": "value1", "key2": "value2"})
    elif base_type == 'object':
        return json.dumps({"field1": "value1", "field2": "value2"})
    
    return "example-value"

def get_default_value(var_config: Dict[str, Any], arg_type: str) -> Any:
    """Convert default value to correct type."""
    if 'default' not in var_config:
        return None
        
    default = var_config['default']
    
    if arg_type == 'str':
        return str(default)
    elif arg_type == 'int':
        return int(default)
    elif arg_type == 'float':
        return float(default)
    elif arg_type == 'bool':
        return bool(default)
    elif arg_type == 'array':
        return list(default)
    
    return default

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
        # Auto-discover variables from the source
        try:
            parser = TerraformModuleParser(
                source_url=module_config['source']['location'],
                ref=module_config['source'].get('version'),
                subfolder=module_config['source'].get('path')
            )
            variables, warnings, errors = parser.get_variables()
            
            # Log any warnings or errors
            for warning in warnings:
                logger.warning(f"Variable discovery warning: {warning}")
            for error in errors:
                logger.error(f"Variable discovery error: {error}")
            
        except Exception as e:
            logger.error(f"Failed to auto-discover variables: {str(e)}")
            variables = {}

        # Prepare content based on action
        if action == 'plan':
            script_name = 'plan.py' if not with_pr else 'plan_with_pr.py'
        else:
            script_name = f'{action}.py'

        # Add pre-script if provided
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

        # Convert discovered variables to tool arguments
        args = []
        for var_name, var_config in variables.items():
            # Map Terraform type to Kubiya SDK Arg type
            arg_type = map_terraform_type_to_arg_type(var_config['type'])
            
            # Generate example value
            example = generate_example(var_name, var_config['type'])
            
            # Get properly typed default value
            default = get_default_value(var_config, arg_type)
            
            # Create argument with enhanced description
            description = (
                f"{var_config['description']}\n\n"
                f"Type: `{var_config['type']}`"
            )
            
            if var_config.get('validation_rules'):
                description += "\nValidation Rules:\n" + "\n".join(
                    f"- {rule}" for rule in var_config['validation_rules']
                )
            
            # For complex types, add JSON format hint
            if var_config['type'] not in ['string', 'number', 'bool']:
                description += "\n\nInput should be a valid JSON string."
            
            args.append(
                Arg(
                    name=var_name,
                    description=description,
                    type=arg_type,
                    required=var_config.get('required', False),
                    default=default,
                    example=example
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
            "GIT_TOKEN",  # For PR creation if needed
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