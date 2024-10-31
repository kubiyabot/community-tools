from kubiya_sdk.tools import Arg, FileSpec
from databricks_workspace_iac.tools.base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
import inspect
from databricks_workspace_iac.tools.scripts import deploy_to_azure
import json
import os
from pathlib import Path

REQUIREMENTS_FILE_CONTENT = """
slack_sdk>=3.19.0
"""

# Define all possible Terraform variables as tool arguments
TF_ARGS = [
    # Required arguments
    Arg(name="workspace_name", description="The name of the Databricks workspace.", required=True),
    Arg(name="location", description="The Azure region for the workspace.", required=True),
    
    # Storage backend configuration
    Arg(name="storage_account_name", description="The name of the storage account to use for the backend.", required=True),
    Arg(name="container_name", description="The name of the container to use for the backend.", required=True),
    Arg(name="resource_group_name", description="The name of the resource group to use for the backend.", required=True),
    
    # Add ARM_SUBSCRIPTION_ID as a required argument
    Arg(name="arm_subscription_id", description="The Azure subscription ID.", required=True),
    
    # Encryption settings
    Arg(name="managed_services_cmk_key_vault_key_id", description="The ID of the key vault key for managed services encryption.", required=False),
    Arg(name="managed_disk_cmk_key_vault_key_id", description="The ID of the key vault key for managed disk encryption.", required=False),
    Arg(name="infrastructure_encryption_enabled", description="Enable infrastructure encryption.", required=False, default="false"),
    
    # Network settings
    Arg(name="no_public_ip", description="Secure cluster connectivity, no public IP.", required=False, default="false"),
    Arg(name="enable_vnet", description="Enable custom VNet use.", required=False, default="false"),
    Arg(name="virtual_network_id", description="The virtual network ID.", required=False),
    Arg(name="private_subnet_name", description="The name of the private subnet.", required=False),
    Arg(name="public_subnet_name", description="The name of the public subnet.", required=False),
    Arg(name="public_subnet_network_security_group_association_id", description="The ID of the public subnet NSG association.", required=False),
    Arg(name="private_subnet_network_security_group_association_id", description="The ID of the private subnet NSG association.", required=False),
    
    # Security settings
    Arg(name="security_profile_enabled", description="Enable security profile.", required=False, default="false"),
    Arg(name="enhanced_monitoring_enabled", description="Enable enhanced monitoring.", required=False, default="false"),
    
    # Update settings
    Arg(name="automatic_update", description="Enable automatic update.", required=False, default="false"),
    Arg(name="restart_no_updates", description="Enable restart even if there are no updates.", required=False, default="false"),
    Arg(name="day_of_week", description="Day of the week to apply updates.", required=False),
    Arg(name="frequency", description="Frequency of updates.", required=False),
    Arg(name="hours", description="Hours of window start time.", required=False, default="1"),
    Arg(name="minutes", description="Minutes of window start time.", required=False, default="0"),
    
    # Network configuration
    Arg(name="address_space", description="The address space for the virtual network.", required=False, default='["10.0.0.0/16"]'),
    Arg(name="address_prefixes_public", description="The address prefix for the public network.", required=False, default='["10.0.2.0/24"]'),
    Arg(name="address_prefixes_private", description="The address prefix for the private network.", required=False, default='["10.0.1.0/24"]'),
    
    # Tags
    Arg(name="tags", description="A JSON string of tags to apply to the workspace.", required=False, default="{}"),
]

def _format_arg_value(arg):
    """Helper function to properly format argument values for JSON."""
    if arg.default is None:
        return None
    
    # Handle boolean values
    if isinstance(arg.default, str):
        if arg.default.lower() == 'true':
            return True
        if arg.default.lower() == 'false':
            return False
    
    # Handle JSON arrays and objects
    if isinstance(arg.default, str) and (arg.default.startswith('[') or arg.default.startswith('{')):
        try:
            return json.loads(arg.default)
        except json.JSONDecodeError:
            return arg.default
    
    # Return other values as is
    return arg.default

def create_deploy_cmd(args):
    """Generate DEPLOY_CMD with placeholders replaced by actual argument values."""
    # Build a dictionary of argument values
    arg_values = {arg.name: args.get(arg.name) or arg.default for arg in TF_ARGS}

    # Create tf_json content
    tf_vars = {k: v for k, v in arg_values.items() if v is not None and k not in [
        "storage_account_name",
        "container_name",
        "resource_group_name",
        "arm_subscription_id",
    ]}
    tf_json = json.dumps(tf_vars, indent=4)

    # Define the deployment command template
    deploy_cmd_template = '''
    # Exit immediately if any command fails
    set -euo pipefail
    
    # Enhanced error handler with more descriptive messages
    error_handler() {{
        local line_no=$1
        local error_code=$2
        echo -e "\\n❌ Deployment failed!"
        echo -e "   ╰─ Error occurred at line $line_no with exit code $error_code"
        
        case $error_code in
            1)
                echo -e "   ╰─ General error - Check the logs above for details"
                ;;
            126|127)
                echo -e "   ╰─ Command not found or permission denied"
                ;;
            137)
                echo -e "   ╰─ Process terminated - Possible memory issues"
                ;;
            *)
                echo -e "   ╰─ Unexpected error occurred"
                ;;
        esac
        
        # Cleanup
        [ -d "$VENV_PATH" ] && rm -rf "$VENV_PATH"
        exit $error_code
    }}
    
    # Set error trap with line number tracking
    trap 'error_handler ${{LINENO}} $?' ERR
    
    # Define variables at the start
    VENV_PATH="/tmp/venv"
    TFVARS_PATH="/tmp/terraform.tfvars.json"
    REQUIREMENTS_PATH="/tmp/requirements.txt"
    
    echo -e "🔧 Setting up deployment environment..."
    
    # Install system dependencies with better error checking
    if ! apk add --no-cache --quiet python3 py3-pip python3-dev py3-virtualenv jq git > /dev/null 2>&1; then
        echo -e "❌ Failed to install system dependencies"
        echo -e "   ╰─ Check if you have sufficient permissions or internet connectivity"
        exit 1
    fi
    
    # Create and activate virtual environment with error checking
    echo -e "   ╰─ Creating Python virtual environment"
    if ! python3 -m venv $VENV_PATH > /dev/null 2>&1; then
        echo -e "❌ Failed to create virtual environment at $VENV_PATH"
        echo -e "   ╰─ Check Python installation and permissions"
        exit 1
    fi
    
    # Source the virtual environment
    . $VENV_PATH/bin/activate
    
    # Upgrade pip silently
    pip install --quiet --upgrade pip > /dev/null 2>&1
    
    # Install requirements in virtual environment
    echo -e "   ╰─ Installing Python dependencies"
    if ! pip install --quiet -r $REQUIREMENTS_PATH > /dev/null 2>&1; then
        echo -e "❌ Failed to install Python requirements. Please check requirements.txt"
        exit 1
    fi
    
    echo -e "📝 Preparing configuration files..."
    echo -e "   ╰─ Generating terraform.tfvars.json"
    
    # Create tfvars file with proper JSON formatting
    cat > $TFVARS_PATH << 'EOL'
    {tf_json}
    EOL
    
    # Validate JSON format
    if ! jq '.' $TFVARS_PATH >/dev/null 2>&1; then
        echo -e "❌ Invalid JSON format in terraform.tfvars.json"
        echo -e "Content of terraform.tfvars.json:"
        cat $TFVARS_PATH
        exit 1
    fi
    
    echo -e "\\n🚀 Initiating Databricks workspace deployment..."
    echo -e "   ╰─ Launching deployment script"
    
    # Export required environment variables
    export WORKSPACE_NAME="{workspace_name}"
    export REGION="{location}"
    export STORAGE_ACCOUNT_NAME="{storage_account_name}"
    export CONTAINER_NAME="{container_name}"
    export RESOURCE_GROUP_NAME="{resource_group_name}"
    export ARM_SUBSCRIPTION_ID="{arm_subscription_id}"
    
    # Run deployment script with full output
    if ! python /tmp/scripts/deploy_to_azure.py $TFVARS_PATH; then
        echo -e "❌ Deployment script failed. Please check the logs above for details."
        exit 1
    fi
    
    # Deactivate virtual environment
    deactivate
    
    echo -e "✅ Deployment completed successfully!"
    '''
    # Replace placeholders in deploy_cmd_template
    deploy_cmd = deploy_cmd_template.format(
        tf_json=tf_json,
        workspace_name=arg_values["workspace_name"],
        location=arg_values["location"],
        storage_account_name=arg_values["storage_account_name"],
        container_name=arg_values["container_name"],
        resource_group_name=arg_values["resource_group_name"],
        arm_subscription_id=arg_values["arm_subscription_id"]
    )
    return deploy_cmd

# Create the tool using the create_deploy_cmd function
azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a Databricks workspace on Azure using Infrastructure as Code (Terraform).",
    content=create_deploy_cmd,
    args=TF_ARGS,
    with_files=[
        FileSpec(
            destination="/tmp/scripts/deploy_to_azure.py",
            content=inspect.getsource(deploy_to_azure),
        ),
        FileSpec(
            destination="/tmp/requirements.txt",
            content=REQUIREMENTS_FILE_CONTENT,
        ),
        # Add Terraform files
        *[
            FileSpec(
                destination=f"/tmp/terraform/azure/{filename}",
                content=content
            )
            for filename, content in TERRAFORM_FILES.items()
        ],
    ],
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant S as System 🖥️
        participant T as Terraform ⚙️
        participant A as Azure ☁️
        participant D as Databricks 🚀

        U ->> S: Start Deployment 🎬
        Note over S: Generate tfvars from input

        S ->> T: Initialize Terraform backend

        T ->> A: Request resources 🏗️
        activate A
        Note over A: Create workspace infrastructure
        A -->> T: Resources provisioned ✅
        deactivate A

        T ->> D: Configure workspace 🔧
        activate D
        Note over D: Set up Databricks environment
        D -->> T: Workspace ready 🌟
        deactivate D

        T -->> S: Deployment complete
        S -->> U: Success! Here's your workspace URL 🎉
    """
)

# Register the tool
tool_registry.register("databricks", azure_db_apply_tool)