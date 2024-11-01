from kubiya_sdk.tools import Arg, FileSpec
from databricks_tools.tools.workspace_creation.base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
import inspect
from databricks_tools.tools.scripts import deploy_to_azure

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

# Create a command that will generate the tfvars file and then run the deployment
DEPLOY_CMD = """
# Exit immediately if any command fails
set -euo pipefail

# Ensure Python output isn't buffered
export PYTHONUNBUFFERED=1

# Enhanced error handler with more descriptive messages
error_handler() {
    local line_no="$1"
    local error_code="$2"
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
}

# Set error trap with line number tracking
trap 'error_handler "$LINENO" "$?"' ERR

# Define variables at the start
VENV_PATH="/tmp/venv"
TFVARS_PATH="/tmp/terraform.tfvars.json"
REQUIREMENTS_PATH="/tmp/requirements.txt"

echo -e "🔧 Setting up deployment environment..."

# Install system dependencies with better error checking
if ! apk add --no-cache --quiet python3 py3-pip python3-dev py3-virtualenv > /dev/null 2>&1; then
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

# Export all arguments as environment variables for Python accessibility
export TFVARS_PATH
export workspace_name
export location
export storage_account_name
export container_name
export resource_group_name
export managed_services_cmk_key_vault_key_id=${managed_services_cmk_key_vault_key_id:-}
export managed_disk_cmk_key_vault_key_id=${managed_disk_cmk_key_vault_key_id:-}
export infrastructure_encryption_enabled=${infrastructure_encryption_enabled:-false}
export no_public_ip=${no_public_ip:-false}
export enable_vnet=${enable_vnet:-false}
export virtual_network_id=${virtual_network_id:-}
export private_subnet_name=${private_subnet_name:-}
export public_subnet_name=${public_subnet_name:-}
export public_subnet_network_security_group_association_id=${public_subnet_network_security_group_association_id:-}
export private_subnet_network_security_group_association_id=${private_subnet_network_security_group_association_id:-}
export security_profile_enabled=${security_profile_enabled:-false}
export enhanced_monitoring_enabled=${enhanced_monitoring_enabled:-false}
export automatic_update=${automatic_update:-false}
export restart_no_updates=${restart_no_updates:-false}
export day_of_week=${day_of_week:-}
export frequency=${frequency:-}
export hours=${hours:-1}
export minutes=${minutes:-0}
export address_space=${address_space:-'["10.0.0.0/16"]'}
export address_prefixes_public=${address_prefixes_public:-'["10.0.2.0/24"]'}
export address_prefixes_private=${address_prefixes_private:-'["10.0.1.0/24"]'}
export tags=${tags:-'{}'}

# Use a Python script to generate terraform.tfvars.json
python - << 'EOF'
import json
import os

tfvars = {
    "workspace_name": os.environ.get("workspace_name"),
    "location": os.environ.get("location"),
    "managed_services_cmk_key_vault_key_id": os.environ.get("managed_services_cmk_key_vault_key_id") or None,
    "managed_disk_cmk_key_vault_key_id": os.environ.get("managed_disk_cmk_key_vault_key_id") or None,
    "infrastructure_encryption_enabled": os.environ.get("infrastructure_encryption_enabled", "false").lower() == "true",
    "no_public_ip": os.environ.get("no_public_ip", "false").lower() == "true",
    "enable_vnet": os.environ.get("enable_vnet", "false").lower() == "true",
    "virtual_network_id": os.environ.get("virtual_network_id") or None,
    "private_subnet_name": os.environ.get("private_subnet_name") or None,
    "public_subnet_name": os.environ.get("public_subnet_name") or None,
    "public_subnet_network_security_group_association_id": os.environ.get("public_subnet_network_security_group_association_id") or None,
    "private_subnet_network_security_group_association_id": os.environ.get("private_subnet_network_security_group_association_id") or None,
    "security_profile_enabled": os.environ.get("security_profile_enabled", "false").lower() == "true",
    "enhanced_monitoring_enabled": os.environ.get("enhanced_monitoring_enabled", "false").lower() == "true",
    "automatic_update": os.environ.get("automatic_update", "false").lower() == "true",
    "restart_no_updates": os.environ.get("restart_no_updates", "false").lower() == "true",
    "day_of_week": os.environ.get("day_of_week") or None,
    "frequency": os.environ.get("frequency") or None,
    "hours": int(os.environ.get("hours", "1")),
    "minutes": int(os.environ.get("minutes", "0")),
    "address_space": json.loads(os.environ.get("address_space", '["10.0.0.0/16"]')),
    "address_prefixes_public": json.loads(os.environ.get("address_prefixes_public", '["10.0.2.0/24"]')),
    "address_prefixes_private": json.loads(os.environ.get("address_prefixes_private", '["10.0.1.0/24"]')),
    "tags": json.loads(os.environ.get("tags", '{}')),
}

# Remove keys with None values
tfvars = {k: v for k, v in tfvars.items() if v is not None}

# Write to terraform.tfvars.json
with open(os.environ['TFVARS_PATH'], 'w') as f:
    json.dump(tfvars, f, indent=2)
EOF

# Validate JSON format
if ! jq '.' "$TFVARS_PATH" >/dev/null 2>&1; then
    echo -e "❌ Invalid JSON format in terraform.tfvars.json"
    echo -e "Content of terraform.tfvars.json:"
    cat "$TFVARS_PATH"
    exit 1
fi

echo -e "\\n🚀 Initiating Databricks workspace deployment..."
echo -e "   ╰─ Launching deployment script"

# Export required environment variables
export WORKSPACE_NAME="$workspace_name"
export LOCATION="$location"
export REGION="$location"
export STORAGE_ACCOUNT_NAME="$storage_account_name"
export CONTAINER_NAME="$container_name"
export RESOURCE_GROUP_NAME="$resource_group_name"

# Run deployment script with full output
if ! python /tmp/scripts/deploy_to_azure.py "$TFVARS_PATH"; then
    echo -e "❌ Deployment script failed. Please check the logs above for details."
    exit 1
fi

# Deactivate virtual environment
deactivate

echo -e "✅ Deployment completed successfully!"
"""

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a Databricks workspace on Azure using Infrastructure as Code (Terraform).",
    content=DEPLOY_CMD,
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

        S ->> S: Clone repository 📦
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