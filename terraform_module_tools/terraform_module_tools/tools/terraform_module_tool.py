from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any
import os
import json

class TerraformTool(Tool):
    """Base class for Terraform tools."""
    def __init__(
        self,
        name: str,
        description: str,
        source_config: Dict[str, Any],
        variable_args: List[Arg] = None,
        action: str = 'plan',
        env: List[str] = None,
        secrets: List[str] = None,
    ):
        # Prepare content based on action
        if action == 'vars':
            content = """
# Show variables
python /opt/scripts/get_module_vars.py '{{ .source_config | toJson }}' || exit 1
"""
        else:
            content = f"""
# Download hcl2json if needed
if ! command -v hcl2json &> /dev/null; then
    curl -L -o /usr/local/bin/hcl2json https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64
    chmod +x /usr/local/bin/hcl2json
fi

# Run Terraform {action}
python /opt/scripts/terraform_{action}.py '{{ .source_config | toJson }}' '{{ .variables | toJson }}' || exit 1
"""

        # Prepare arguments
        args = []
        if action not in ['vars']:  # Plan and apply need variable arguments
            args.extend(variable_args or [])
        
        # Add source config argument
        args.append(
            Arg(
                name="source_config",
                description="Module source configuration",
                required=True,
                type="object",
                default=source_config
            )
        )

        # Get script files
        script_files = {}
        scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
        for script_name in os.listdir(scripts_dir):
            if script_name.endswith('.py'):
                with open(os.path.join(scripts_dir, script_name), 'r') as f:
                    script_files[script_name] = f.read()

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            env=env or [],
            secrets=secrets or [],
            with_files=[
                FileSpec(
                    destination=f"/opt/scripts/{script_name}",
                    content=script_content
                )
                for script_name, script_content in script_files.items()
            ]
        )

def create_terraform_tool(
    name: str,
    description: str,
    source_config: Dict[str, Any],
    variable_args: List[Arg] = None,
    action: str = 'plan',
    env: List[str] = None,
    secrets: List[str] = None,
) -> TerraformTool:
    """
    Create a Terraform tool with the specified configuration.
    
    Args:
        name: Tool name
        description: Tool description
        source_config: Module source configuration
        variable_args: List of variable arguments
        action: Tool action (plan, apply, vars)
        env: Required environment variables
        secrets: Required secrets
    
    Returns:
        Configured TerraformTool instance
    """
    return TerraformTool(
        name=name,
        description=description,
        source_config=source_config,
        variable_args=variable_args,
        action=action,
        env=env,
        secrets=secrets,
    )

# Export the create function
__all__ = ['create_terraform_tool']