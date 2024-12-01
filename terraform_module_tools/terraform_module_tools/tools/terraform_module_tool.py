from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any
import os
import json
import logging
from pathlib import Path
from ..parser import TerraformModuleParser
from pydantic import Field, root_validator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

def truncate_description(description: str, var_config: dict) -> str:
    """Truncate description and add default/optional information."""
    if not description:
        description = "No description provided"
    
    # Add optional/required status
    status = "Optional" if not var_config.get('required', False) else "Required"
    description = f"{description}\n[{status}]"
    
    # Add default value if present
    if 'default' in var_config and var_config['default'] is not None:
        default_str = str(var_config['default'])
        if isinstance(var_config['default'], (dict, list)):
            default_str = json.dumps(var_config['default'])
        description = f"{description}\n(Default value if not passed: {default_str})"

    # Add JSON format example for complex types
    if var_config['type'] not in ['string', 'number', 'bool']:
        example = None
        if 'list' in var_config['type'].lower():
            example = '["item1", "item2"]'
            if var_config['default']:
                example = json.dumps(var_config['default'])
        elif 'map' in var_config['type'].lower() or 'object' in var_config['type'].lower():
            example = '{"key1": "value1", "key2": "value2"}'
            if var_config['default']:
                example = json.dumps(var_config['default'])
        
        if example:
            description = f"{description}\nProvide as JSON string, example: {example}"
        else:
            description = f"{description}\nProvide as JSON string"

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return description[:MAX_DESCRIPTION_LENGTH-3] + "..."
    return description

class TerraformModuleTool(Tool):
    """Base class for Terraform module tools."""
    module_config: Dict[str, Any]
    action: str = 'plan'
    with_pr: bool = False
    env: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    with_files: List[FileSpec] = Field(default_factory=list)

    @root_validator(pre=True)
    def initialize_tool(cls, values):
        name = values.get('name')
        module_config = values.get('module_config')
        action = values.get('action', 'plan')
        with_pr = values.get('with_pr', False)
        env = values.get('env') or []
        secrets = values.get('secrets') or []

        logger.info(f"Creating tool for module: {name}")

        # Existing logic from your __init__ method
        # Parse variables using TerraformModuleParser
        try:
            logger.info(f"Discovering variables from: {module_config['source']['location']}")
            parser = TerraformModuleParser(
                source_url=module_config['source']['location'],
                ref=module_config['source'].get('version'),
                max_workers=8
            )
            variables, warnings, errors = parser.get_variables()

            if errors:
                for error in errors:
                    logger.error(f"Variable discovery error: {error}")
                raise ValueError(f"Failed to discover variables: {errors[0]}")

            for warning in warnings:
                logger.warning(f"Variable discovery warning: {warning}")

            if not variables:
                raise ValueError(f"No variables found in module {name}")

            logger.info(f"Found {len(variables)} variables")

        except Exception as e:
            logger.error(f"Failed to auto-discover variables: {str(e)}", exc_info=True)
            raise ValueError(f"Variable discovery failed: {str(e)}")

        # Convert variables to args list
        args = []
        for var_name, var_config in variables.items():
            try:
                # Map to supported type
                arg_type = map_terraform_type_to_arg_type(var_config['type'])
                logger.debug(f"Mapping variable {var_name} of type {var_config['type']} to {arg_type}")

                # Create description with optional/required status and default value
                description = truncate_description(
                    var_config.get('description', 'No description'),
                    var_config
                )

                # Create Arg object
                arg = Arg(
                    name=var_name,
                    description=description,
                    type=arg_type,
                    required=var_config.get('required', False)
                )

                # Handle default value conversion
                if 'default' in var_config and var_config['default'] is not None:
                    default_value = var_config['default']

                    # Convert default value to string based on type
                    if arg_type == 'str':
                        if isinstance(default_value, (dict, list)):
                            arg.default = json.dumps(default_value)
                        else:
                            arg.default = str(default_value)
                    elif arg_type == 'int':
                        try:
                            arg.default = str(int(float(default_value)))
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert default value for {var_name} to int, setting to '0'")
                            arg.default = '0'
                    elif arg_type == 'bool':
                        # Convert boolean to string 'true' or 'false'
                        arg.default = str(default_value).lower()

                args.append(arg)
                logger.info(f"Added argument: {var_name} ({arg_type}) with default: {arg.default}")

            except Exception as e:
                logger.error(f"Failed to process variable {var_name}: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to process variable {var_name}: {str(e)}")

        if not args:
            raise ValueError(f"No valid arguments created for module {name}")

        # Prepare tool description
        action_desc = {
            'plan': 'Plan infrastructure changes for',
            'apply': 'Apply infrastructure changes to',
            'plan_pr': 'Plan infrastructure changes and create PR for'
        }
        current_action = 'plan_pr' if action == 'plan' and with_pr else action
        tool_description = f"{action_desc[current_action]} {module_config['description']} (original source code: {module_config['source']['location']}) - version: {module_config['source'].get('version', 'unknown')} - This tool is managed by Kubiya and may not be updated to the latest version of the module. Please check the original source code for the latest version."

        # Prepare script content
        script_name = 'plan_with_pr.py' if action == 'plan' and with_pr else f'terraform_{action}.py'

        # Read the existing script files
        script_files = {}
        scripts_needed = [
            script_name,
            'prepare_tfvars.py',
            'terraform_handler.py'
        ]
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name in scripts_needed or script_file.name == 'terraform_handler.py':
                script_files[script_file.name] = script_file.read_text()

        if not script_files:
            raise ValueError("No script files found")

        # Create FileSpec objects for scripts
        with_files = []
        for s_name, s_content in script_files.items():
            dest_path = f"/opt/scripts/{s_name}"
            with_files.append(FileSpec(destination=dest_path, content=s_content))

        # Save module variables signature to a file
        module_variables_signature = json.dumps(variables, indent=2)
        module_variables_file = FileSpec(
            destination="/opt/module_variables.json",
            content=module_variables_signature
        )
        with_files.append(module_variables_file)

        # Update 'with_files' in values
        values['with_files'] = with_files

        # Prepare the shell content script
        content = f"""
set -e

# Make scripts executable
chmod +x /opt/scripts/*.py

# Prepare terraform.tfvars.json
echo "🔧 Preparing terraform variables..."
python3 /opt/scripts/prepare_tfvars.py /opt/module_variables.json

# Check if terraform.tfvars.json was created
if [ ! -f terraform.tfvars.json ]; then
    echo "❌ Failed to create terraform.tfvars.json."
    exit 1
fi

# Run Terraform {action}
echo "🚀 Running Terraform {action}..."
python3 /opt/scripts/{script_name}
"""

        # Update values dictionary
        values.update({
            'description': tool_description,
            'content': content,
            'args': args,
            'env': env + ["SLACK_CHANNEL_ID", "SLACK_THREAD_TS"],
            'secrets': secrets + ["SLACK_API_TOKEN", "GH_TOKEN"],
            'type': "docker",
            'image': "hashicorp/terraform:latest",
            'icon_url': "https://user-images.githubusercontent.com/31406378/108641411-f9374f00-7496-11eb-82a7-0fa2a9cc5f93.png",
        })

        return values
