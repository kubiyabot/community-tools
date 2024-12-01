from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any
import os
from pathlib import Path

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
        # Prepare content based on action
        if action == 'plan':
            script_name = 'plan.py' if not with_pr else 'plan_with_pr.py'
        else:
            script_name = f'{action}.py'

        content = f"""
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
            args.append(
                Arg(
                    name=var_name,
                    description=var_config['description'],
                    type=var_config['type'].split('(')[0],  # Handle list(string) -> list
                    required=var_config.get('required', False),
                    default=var_config.get('default')
                )
            )

        # Get script files
        script_files = {}
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name.endswith('.py'):
                script_files[script_file.name] = script_file.read_text()

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