from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
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

        # Read all script files from the scripts directory
        script_files = {}
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        required_files = {
            # Core script files
            'terraform_plan.py',
            'terraform_apply.py',
            'prepare_tfvars.py',
            'terraform_handler.py',
            'get_module_vars.py',
            'error_handler.py',
            # Config files
            'configs/module_configs.json',
            # Requirements file
            'requirements.txt'
        }

        # Create FileSpec objects for all required files
        with_files = []
        for filename in required_files:
            file_path = scripts_dir / filename
            if file_path.exists():
                dest_path = f"/opt/scripts/{filename}"
                # Add the actual file
                with_files.append(FileSpec(
                    destination=dest_path,
                    content=file_path.read_text()
                ))
            else:
                logger.warning(f"Required script file not found: {filename}")

        # Save module variables signature to a file
        module_variables_signature = json.dumps(variables, indent=2)
        module_variables_file = FileSpec(
            destination="/opt/module_variables.json",
            content=module_variables_signature
        )
        with_files.append(module_variables_file)

        # Save module configuration for runtime use
        module_config_file = FileSpec(
            destination="/opt/scripts/.module_config.json",
            content=json.dumps(values.get('module_config', {}))
        )
        with_files.append(module_config_file)

        # Update 'with_files' in values
        values['with_files'] = with_files

        # Get Terraform version from environment or use latest
        tf_version = os.environ.get("TERRAFORM_VERSION", "1.10.0")
        
        # Get module path from source config
        module_path = module_config['source'].get('path', '')
        
        content = f"""#!/bin/sh
# Exit on error and unset variables
set -eu

# Install Terraform if not already installed
install_terraform() {{
    if command -v terraform >/dev/null 2>&1; then
        current_version=$(terraform version | head -n1 | cut -d'v' -f2)
        if [ "$current_version" = "{tf_version}" ]; then
            printf "✅ Terraform {tf_version} is already installed\\n"
            return 0
        fi
    fi

    printf "📦 Installing Terraform {tf_version}...\\n"

    # Create bin directory
    mkdir -p /usr/local/bin

    # Download Terraform binary
    if ! curl -fsSL "https://releases.hashicorp.com/terraform/{tf_version}/terraform_{tf_version}_linux_amd64.zip" -o /tmp/terraform.zip; then
        printf "❌ Failed to download Terraform\\n" >&2
        return 1
    fi

    # Install unzip if not present
    if ! command -v unzip >/dev/null 2>&1; then
        apk add unzip >/dev/null 2>&1 || {{
            printf "❌ Failed to install unzip\\n" >&2
            return 1
        }}
    fi

    # Extract Terraform binary
    if ! unzip -o /tmp/terraform.zip -d /usr/local/bin >/dev/null 2>&1; then
        printf "❌ Failed to extract Terraform binary\\n" >&2
        return 1
    fi
    
    # Make binary executable
    chmod +x /usr/local/bin/terraform

    # Cleanup
    rm -f /tmp/terraform.zip

    # Verify installation
    if ! terraform version | grep -q "{tf_version}"; then
        printf "❌ Terraform installation verification failed\\n" >&2
        return 1
    fi

    printf "✅ Successfully installed Terraform {tf_version}\\n"
    return 0
}}

# Install system dependencies
printf "📦 Installing system dependencies...\\n"
apk add curl git > /dev/null 2>&1 || {{
    printf "❌ Failed to install system dependencies\\n" >&2
    exit 1
}}

# Install Terraform
if ! install_terraform; then
    printf "❌ Failed to install Terraform\\n" >&2
    exit 1
fi

# Validate required environment variables
if [ -z "$KUBIYA_USER_EMAIL" ]; then
    printf "❌ KUBIYA_USER_EMAIL environment variable is required\\n" >&2
    exit 1
fi

# Generate workspace name from email
WORKSPACE_NAME=$(printf "%s" "$KUBIYA_USER_EMAIL" | tr '[:upper:]' '[:lower:]' | sed 's/@/-/g; s/\\./-/g')
WORKSPACE_NAME="$(printf "%.30s" "$WORKSPACE_NAME")-{action}"
export WORKSPACE_NAME

printf "🔧 Using workspace name: %s\\n" "$WORKSPACE_NAME"

# Working directory setup
WORK_DIR="/workspace/$WORKSPACE_NAME"
REPO_NAME=$(basename {module_config['source']['location']} .git)
MODULE_DIR="$WORK_DIR/$REPO_NAME{f'/{module_path}' if module_path else ''}"

# Create workspace directory
mkdir -p "$WORK_DIR"

# Clone repository
printf "📦 Cloning module repository...\\n"
if [ -n "${{GH_TOKEN:-}}" ]; then
    REPO_URL=$(printf "%s" "{module_config['source']['location']}" | sed "s#https://#https://$GH_TOKEN@#")
else
    REPO_URL="{module_config['source']['location']}"
fi

git clone --depth 1 "$REPO_URL" "$WORK_DIR/$REPO_NAME"

# Validate module directory
if [ ! -d "$MODULE_DIR" ]; then
    printf "❌ Module directory not found: %s\\n" "$MODULE_DIR" >&2
    printf "Contents of %s:\\n" "$WORK_DIR/$REPO_NAME"
    ls -la "$WORK_DIR/$REPO_NAME"
    
    if [ -n "{module_path}" ]; then
        printf "\\nAvailable directories in repository:\\n"
        find "$WORK_DIR/$REPO_NAME" -type d -not -path '*/\.*'
    fi
    exit 1
fi

# Check for Terraform files
printf "Checking for Terraform files in %s\\n" "$MODULE_DIR"
TF_FILES=$(find "$MODULE_DIR" -maxdepth 1 -type f -name "*.tf" | wc -l)
if [ "$TF_FILES" -eq 0 ]; then
    printf "❌ No Terraform files found in module directory: %s\\n" "$MODULE_DIR" >&2
    printf "Contents of %s:\\n" "$MODULE_DIR"
    ls -la "$MODULE_DIR"
    printf "\\nAvailable .tf files in repository:\\n"
    find "$WORK_DIR/$REPO_NAME" -name "*.tf"
    exit 1
else
    printf "Found %d Terraform files in module directory\\n" "$TF_FILES"
fi

cd "$MODULE_DIR"
printf "📍 Working in directory: %s\\n" "$MODULE_DIR"

# List found Terraform files for verification
printf "Terraform files in working directory:\\n"
ls -l *.tf

# Set up Python environment
printf "📦 Setting up Python environment...\\n"

# Create Python package structure
mkdir -p /opt/scripts/terraform_tools
mv /opt/scripts/*.py /opt/scripts/terraform_tools/
mv /opt/scripts/configs /opt/scripts/terraform_tools/
touch /opt/scripts/terraform_tools/__init__.py

# Install the package in development mode
cd /opt/scripts
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="terraform_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "slack-sdk",
        "pydantic",
        "pyyaml",
        "requests"
    ]
)
EOF

# Install package and dependencies
printf "📦 Installing package and dependencies...\\n"
pip3 install -e . || {{
    printf "❌ Failed to install package\\n" >&2
    exit 1
}}

# Export module path for scripts
export MODULE_PATH="$MODULE_DIR"
export MODULE_VARS_FILE="/opt/module_variables.json"

# Prepare terraform.tfvars.json
printf "🔧 Preparing terraform variables...\\n"
python3 -m terraform_tools.prepare_tfvars || {{
    printf "❌ Failed to prepare terraform variables\\n" >&2
    exit 1
}}

# Verify tfvars file was created
if [ ! -f "$MODULE_DIR/terraform.tfvars.json" ]; then
    printf "❌ Failed to create terraform.tfvars.json\\n" >&2
    exit 1
fi

# Run Terraform action
printf "🚀 Running Terraform {action}...\\n"
python3 -m terraform_tools.{script_name[:-3]}
"""
        mermaid_diagram = f"""
sequenceDiagram
    participant U as 👤 User
    participant B as 🤖 Bot
    participant V as 🔍 Parser
    participant T as 🏗️ Terraform
    participant G as 📦 Git/PR
    participant A as ✅ Approver

    Note over U,A: 🚀 Terraform Self-Service Flow

    U->>B: 💬 "Need new env in eu-west-1!"

    rect rgb(240, 240, 240)
        Note over B,V: 📝 Parse & Prep
        B->>V: Read Request
        V->>V: Get Variables
        V->>V: Set Defaults
        V->>B: Ready!
    end

    rect rgb(235, 245, 255)
        Note over B,U: ⚙️ Setup
        B->>U: Missing info?
        U->>B: Here you go!
        B->>B: Quick check
    end

    rect rgb(245, 240, 255)
        Note over B,T: 📋 Plan
        B->>T: Init
        T->>T: Load config
        T->>T: Make plan
        T-->>B: Plan ready!
    end

    alt PR Wanted 📬
        B->>G: New PR
        B->>G: Add plan
        Note over G: 🎯 PR Ready!
    end

    alt Need Approval 🔒
        B->>A: Please review
        
        alt Approved ✨
            A->>B: Good to go!
            B->>T: Apply now
            T-->>B: Done!
            B->>U: 🎉 All set!
        else Rejected ❌
            A->>B: Nope
            B->>U: 😕 Rejected
        end
    else Direct Apply ⚡
        B->>T: Do it!
        T-->>B: Complete
        B->>U: 🎉 Ready!
    end

    Note over U,B: 🏁 All Done!
"""

        # Update values dictionary with KUBIYA_USER_EMAIL requirement and new base image
        values.update({
            'description': tool_description,
            'content': content,
            'args': args,
            'env': env + ["SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "KUBIYA_USER_EMAIL"],
            'secrets': secrets + ["SLACK_API_TOKEN", "GH_TOKEN"],
            'type': "docker",
            'mermaid': mermaid_diagram,
            'image': "python:3.9-alpine",  # Using Python Alpine as base image
            'icon_url': "https://user-images.githubusercontent.com/31406378/108641411-f9374f00-7496-11eb-82a7-0fa2a9cc5f93.png",
        })

        # Get provider requirements
        required_env, required_files = parser.get_provider_requirements()
        
        # Add provider-specific requirements to values
        values['env'] = (env or []) + required_env + ["SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "KUBIYA_USER_EMAIL"]
        values['with_files'] = (with_files or []) + required_files

        return values