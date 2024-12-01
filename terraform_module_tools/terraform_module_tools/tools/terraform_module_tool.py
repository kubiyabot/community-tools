from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pathlib import Path
from ..parser import TerraformModuleParser

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

def truncate_description(description: str) -> str:
    """Truncate description to max length."""
    if not description:
        return "No description provided"
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return description[:MAX_DESCRIPTION_LENGTH-3] + "..."
    return description

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
        logger.info(f"Creating tool for module: {name}")
        
        if not module_config.get('source', {}).get('location'):
            raise ValueError(f"Module {name} is missing source location")
        
        # Auto-discover variables
        try:
            logger.info(f"Discovering variables from: {module_config['source']['location']}")
            parser = TerraformModuleParser(
                source_url=module_config['source']['location'],
                ref=module_config['source'].get('version'),
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
                
                # Create short description
                description = truncate_description(
                    f"{var_config.get('description', 'No description')} (Type: {var_config['type']})"
                )
                
                # Add JSON hint for complex types
                if var_config['type'] not in ['string', 'number', 'bool']:
                    description = truncate_description(
                        f"{description}\nProvide as JSON string"
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
        
        # Prepare tool description based on the config and action
        action_desc = {
            'plan': 'Plan infrastructure changes for',
            'apply': 'Apply infrastructure changes to', 
            'plan_pr': 'Plan infrastructure changes and create PR for'
        }
        current_action = 'plan_pr' if action == 'plan' and with_pr else action
        tool_description = f"{action_desc[current_action]} {module_config['description']} (original source code: {module_config['source']['location']}) - version: {module_config['source'].get('version', 'unknown')} - This tool is managed by Kubiya and may not be updated to the latest version of the module. Please check the original source code for the latest version."

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

        # Get script files
        script_files = {}
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name.endswith('.py'):
                script_files[script_file.name] = script_file.read_text()

        if not script_files:
            raise ValueError("No script files found")

        # Add common environment variables and secrets
        env = (env or []) + [
            "SLACK_CHANNEL_ID",
            "SLACK_THREAD_TS",
            "GIT_TOKEN",
        ]
        
        secrets = (secrets or []) + [
            "SLACK_API_TOKEN",
        ]

        logger.info(f"Initializing tool {name} with {len(args)} arguments")
        super().__init__(
            name=name,
            description=tool_description,
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