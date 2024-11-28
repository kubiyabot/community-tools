import os
from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from ..scripts.config_loader import load_terraform_configs
from typing import Dict, Any, List
from .base import TerraformTool
from ..scripts.module_scanner import TerraformModuleScanner
from pathlib import Path

def create_terraform_tool(module_name: str, config: Dict[str, Any], action: str) -> TerraformTool:
    """Create a Terraform tool for a specific module and action."""
    
    args = []
    content = ""
    with_files = []
    module_files = []
    module_path = config.get('file_path')

    # Prepare working directory variable for use in scripts
    WORK_DIR = f"/tmp/terraform_{module_name}"

    # Check if a custom script is provided
    if 'script' in config:
        # Use the custom script as content
        content = config['script']

        # Process variables if any
        if 'variables' in config:
            for var in config['variables']:
                args.append(
                    Arg(
                        name=var['name'],
                        type=var.get('type', 'str'),
                        description=var.get('description', ''),
                        required=var.get('required', False),
                        default=var.get('default')
                    )
                )
        # Set action to 'execute' for custom scripts
        action = 'execute'

        # Include any files from the module directory
        if module_path:
            module_dir = os.path.dirname(module_path)
            for root, dirs, files in os.walk(module_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, module_dir)
                    with_files.append(
                        FileSpec(
                            source=file_path,
                            destination=os.path.join("/opt/module_files", rel_path)
                        )
                    )
            # Ensure the script knows where the files are
            content = f"""#!/bin/bash
set -e

# Copy module files to working directory
mkdir -p {WORK_DIR}
cp -R /opt/module_files/* {WORK_DIR}/
cd {WORK_DIR}

""" + content

    else:
        # Proceed with standard Terraform handling
        scanner = TerraformModuleScanner()

        # Determine source type
        source = config.get('source')
        version = config.get('version')
        if source.startswith(('http://', 'https://', 'git://', 'git@')):
            source_type = 'git'
        else:
            source_type = 'registry'

        # Scan module to get variables
        scan_result = scanner.scan_module(
            source_type=source_type,
            source_url=source,
            ref=version
        )
        variables = scan_result.get('variables', {})

        # Convert variables to tool arguments
        for var_name, var_config in variables.items():
            args.append(
                Arg(
                    name=var_name,
                    type="str",  # Simplify all types to strings for user input
                    description=var_config.get('description', ''),
                    required=(var_config.get('required', False) and 'default' not in var_config),
                    default=var_config.get('default')
                )
            )
        
        # Add common arguments
        args.extend([
            Arg(
                name="workspace",
                type="str",
                description="Terraform workspace to use",
                required=False,
                default="default"
            ),
            Arg(
                name="auto_approve",
                type="bool",
                description="Skip interactive approval of plan/apply",
                required=False,
                default=False
            )
        ])
        
        # Prepare the shell script content for the tool
        content = f"""#!/bin/bash
set -e

echo "🚀 Starting Terraform {action} for module: {config['name']}"

# Create working directory
WORK_DIR="{WORK_DIR}"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

"""

        # Include any files from the module directory
        if module_path:
            module_dir = os.path.dirname(module_path)
            for root, dirs, files in os.walk(module_dir):
                for file in files:
                    if file.endswith('.tf') or file.endswith('.tf.json') or file.endswith('.tfvars'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, module_dir)
                        with_files.append(
                            FileSpec(
                                source=file_path,
                                destination=os.path.join("/opt/module_files", rel_path)
                            )
                        )
            # Copy module files to working directory
            content += f"""
# Copy module files to working directory
mkdir -p {WORK_DIR}
cp -R /opt/module_files/* {WORK_DIR}/
"""
        # Create the main.tf file if not included
        main_tf_exists = any(f.destination.endswith('main.tf') for f in with_files)
        if not main_tf_exists:
            content += f"""cat <<'EOF' > main.tf
module "{module_name}" {{
  source = "{source}"
"""
            # Add variables to main.tf
            for var_name in variables:
                content += f'  {var_name} = var.{var_name}\n'
            content += "}\nEOF\n"

        # Generate variables.tf file
        variables_tf_exists = any(f.destination.endswith('variables.tf') for f in with_files)
        if not variables_tf_exists:
            content += "cat <<EOF > variables.tf\n"
            for var_name, var_config in variables.items():
                content += f'variable "{var_name}" {{\n'
                content += f'  type = any\n'  # Use 'any' type for simplicity
                if 'description' in var_config:
                    content += f'  description = "{var_config["description"]}"\n'
                if 'default' in var_config:
                    default_value = var_config['default']
                    if isinstance(default_value, str):
                        default_value = f'"{default_value}"'
                    content += f'  default = {default_value}\n'
                content += "}\n"
            content += "EOF\n"

        # Create terraform.tfvars file
        content += "cat <<EOF > terraform.tfvars\n"
        for arg in args:
            if arg.name in variables:
                content += f'{arg.name} = "{{{{ .{arg.name} }}}}"\n'
        content += "EOF\n"

        # Initialize Terraform
        content += """
# Initialize Terraform
terraform init -input=false

# Select or create workspace
terraform workspace select "{{ .workspace }}" || terraform workspace new "{{ .workspace }}"
"""

        # Execute the action
        if action == "plan":
            content += """
# Run Terraform plan
terraform plan -var-file=terraform.tfvars
"""
        elif action == "apply":
            content += """
# Run Terraform apply
if [ "{{ .auto_approve }}" = "true" ]; then
    terraform apply -var-file=terraform.tfvars -auto-approve
else
    terraform apply -var-file=terraform.tfvars
fi
"""
        elif action == "destroy":
            content += """
# Run Terraform destroy
if [ "{{ .auto_approve }}" = "true" ]; then
    terraform destroy -var-file=terraform.tfvars -auto-approve
else
    terraform destroy -var-file=terraform.tfvars
fi
"""

    # Define the tool
    tool_name = f"{module_name}_{action}"
    tool_description = f"{action.capitalize()} for {config['name']}"

    terraform_tool = TerraformTool(
        name=tool_name,
        description=tool_description,
        content=content,
        args=args,
        with_files=with_files
    )

    return terraform_tool

def initialize_dynamic_tools():
    """Initialize all dynamic Terraform tools based on configuration."""
    configs = load_terraform_configs()
    
    for module_name, config in configs.items():
        if 'script' in config:
            # Custom script-based module
            tool = create_terraform_tool(module_name, config, 'execute')
            tool_registry.register("terraform", tool)
        else:
            # Generate tools for plan, apply, destroy
            for action in ["plan", "apply", "destroy"]:
                tool = create_terraform_tool(module_name, config, action)
                tool_registry.register("terraform", tool)

initialize_dynamic_tools()
