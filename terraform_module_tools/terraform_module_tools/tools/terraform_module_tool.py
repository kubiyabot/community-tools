from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
from ..parser import TerraformModuleParser

def generate_example_value(var_name: str, tf_type: str, var_config: Dict[str, Any]) -> str:
    """Generate contextual example value based on variable name and type."""
    # Extract base type and nested type if present
    base_type = tf_type.split('(')[0].lower()
    nested_type = None
    if '(' in tf_type and ')' in tf_type:
        nested_type = tf_type[tf_type.index('(')+1:tf_type.rindex(')')].lower()

    # Common patterns in variable names
    name_patterns = {
        'name': 'example-resource-name',
        'region': 'us-west-2',
        'zone': 'us-west-2a',
        'environment': 'production',
        'cidr': '10.0.0.0/16',
        'subnet': ['10.0.1.0/24', '10.0.2.0/24'],
        'port': 8080,
        'enabled': True,
        'count': 2,
        'size': 'medium',
        'type': 'gp2',
        'tag': {'Environment': 'production', 'Project': 'example'},
        'arn': 'arn:aws:iam::123456789012:role/example-role',
        'id': 'i-1234567890abcdef0',
        'version': '1.0.0'
    }

    # Check if we have a specific example in the variable config
    if 'example' in var_config:
        return str(var_config['example'])

    # Check for common patterns in the variable name
    for pattern, example in name_patterns.items():
        if pattern in var_name.lower():
            if isinstance(example, (list, dict)):
                return json.dumps(example)
            return str(example)

    # Type-specific examples
    if base_type == 'list' or base_type == 'set':
        if nested_type == 'string':
            return '["value1", "value2"]'
        elif nested_type == 'number':
            return '[1, 2, 3]'
        elif nested_type == 'bool':
            return '[true, false]'
        return '["example1", "example2"]'
    
    elif base_type == 'map':
        if nested_type == 'string':
            return '{"key1": "value1", "key2": "value2"}'
        elif nested_type == 'number':
            return '{"key1": 1, "key2": 2}'
        elif nested_type == 'bool':
            return '{"key1": true, "key2": false}'
        return '{"example_key": "example_value"}'
    
    elif base_type == 'object':
        # Try to create a meaningful example based on the object's structure
        if 'object_attributes' in var_config:
            example_obj = {}
            for attr_name, attr_config in var_config['object_attributes'].items():
                example_obj[attr_name] = generate_example_value(
                    attr_name, 
                    attr_config['type'],
                    attr_config
                )
            return json.dumps(example_obj, indent=2)
        return '{"attribute1": "value1", "attribute2": "value2"}'
    
    # Basic types
    elif base_type == 'string':
        return f'example-{var_name}'
    elif base_type == 'number':
        return '42'
    elif base_type == 'bool':
        return 'true'
    
    return 'example-value'

def map_terraform_type_to_arg_type(tf_type: str) -> str:
    """Map Terraform types to Kubiya SDK Arg types."""
    base_type = tf_type.split('(')[0].lower()
    
    type_mapping = {
        'string': 'str',
        'number': 'float',
        'bool': 'bool',
        'list': 'array',
        'set': 'array',
        'map': 'str',  # Maps will be passed as JSON strings
        'object': 'str',  # Complex objects will be passed as JSON strings
        'any': 'str',
    }
    
    return type_mapping.get(base_type, 'str')

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
        auto_discover: bool = False
    ):
        # Auto-discover variables if requested
        if auto_discover and 'source' in module_config:
            try:
                parser = TerraformModuleParser(
                    source_url=module_config['source'],
                    ref=module_config.get('ref'),
                    subfolder=module_config.get('subfolder')
                )
                variables, warnings, errors = parser.get_variables()
                if variables:
                    module_config['variables'] = variables
                    for warning in warnings:
                        logger.warning(f"Variable discovery warning: {warning}")
                    for error in errors:
                        logger.error(f"Variable discovery error: {error}")
            except Exception as e:
                logger.error(f"Failed to auto-discover variables: {str(e)}")

        # Prepare content based on action
        if action == 'plan':
            script_name = 'plan.py' if not with_pr else 'plan_with_pr.py'
        else:
            script_name = f'{action}.py'

        content = f"""
# Install required packages
pip install -q slack_sdk requests

# Download hcl2json if needed
if ! command -v hcl2json &> /dev/null; then
    curl -L -o /usr/local/bin/hcl2json https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64
    chmod +x /usr/local/bin/hcl2json
fi

# Run Terraform {action}
python /opt/scripts/{script_name} '{{{{ .module_config | toJson }}}}' '{{{{ .variables | toJson }}}}' || exit 1
"""

        # Convert module variables to tool arguments
        args = []
        for var_name, var_config in module_config['variables'].items():
            # Map Terraform type to Kubiya SDK Arg type
            arg_type = map_terraform_type_to_arg_type(var_config['type'])
            
            # Generate example value
            example = generate_example_value(var_name, var_config['type'], var_config)
            
            # Create argument with enhanced description including type and example
            description = (
                f"{var_config['description']}\n\n"
                f"Type: `{var_config['type']}`\n"
                f"Example: `{example}`"
            )
            
            if var_config.get('validation_rules'):
                description += "\nValidation Rules:\n" + "\n".join(
                    f"- {rule}" for rule in var_config['validation_rules']
                )
            
            args.append(
                Arg(
                    name=var_name,
                    description=description,
                    type=arg_type,
                    required=var_config.get('required', False),
                    default=var_config.get('default'),
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