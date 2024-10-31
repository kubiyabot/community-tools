from kubiya_sdk.tools import Arg, FileSpec
from databricks_workspace_iac.tools.base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
import inspect
from databricks_workspace_iac.tools.scripts import deploy_to_azure

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
echo -e "📝 Preparing configuration files..."
echo -e "   ╰─ Generating terraform.tfvars.json"
# Create tfvars file from arguments
echo '{tfvars}' > /tmp/terraform.tfvars.json

echo -e "\n🚀 Initiating Databricks workspace deployment..."
echo -e "   ╰─ Launching deployment script"
# Run deployment script
python /tmp/scripts/deploy_to_azure.py /tmp/terraform.tfvars.json
"""

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a Databricks workspace on Azure using Infrastructure as Code (Terraform).",
    content=DEPLOY_CMD,
    args=TF_ARGS,
    files=[
        FileSpec(
            destination="/tmp/scripts/deploy_to_azure.py",
            content=inspect.getsource(deploy_to_azure),
        ),
    ],
    requirements=["slack_sdk>=3.19.0"],
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