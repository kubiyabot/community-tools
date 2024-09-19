from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/azure

terraform init  -backend-config="storage_account_name={{ .storage_account_name}}" \
  -backend-config="container_name={{ .container_name}}" \
  -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \
  -backend-config="resource_group_name={{ .resource_group_name}}" \
  -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}"
terraform apply -auto-approve \
  -var "workspace_name={{ .workspace_name }}" \
  -var "region={{ .region }}" \
  -var "managed_services_cmk_key_vault_key_id={{ .managed_services_cmk_key_vault_key_id }}" \
  -var "managed_disk_cmk_key_vault_key_id={{ .managed_disk_cmk_key_vault_key_id }}" \
  -var "infrastructure_encryption_enabled={{ .infrastructure_encryption_enabled }}" \
  -var "no_public_ip={{ .no_public_ip }}" \
  -var "enable_vnet={{ .enable_vnet }}" \
  -var "virtual_network_id={{ .virtual_network_id }}" \
  -var "private_subnet_name={{ .private_subnet_name }}" \
  -var "public_subnet_name={{ .public_subnet_name }}" \
  -var "public_subnet_network_security_group_association_id={{ .public_subnet_network_security_group_association_id }}" \
  -var "private_subnet_network_security_group_association_id={{ .private_subnet_network_security_group_association_id }}" \
  -var "storage_account_name={{ .storage_account_name }}" \
  -var "security_profile_enabled={{ .security_profile_enabled }}" \
  -var "enhanced_monitoring_enabled={{ .enhanced_monitoring_enabled }}" \
  -var "azure_client_id=${ARM_CLIENT_ID}" \
  -var "azure_client_secret=${ARM_CLIENT_SECRET}" \
  -var "azure_tenant_id=${ARM_TENANT_ID}" \
  -var "automatic_update={{ .automatic_update }}" \
  -var "restart_no_updates={{ .restart_no_updates }}" \
  -var "day_of_week={{ .day_of_week }}" \
  -var "frequency={{ .frequency }}" \
  -var "hours={{ .hours }}" \
  -var "minutes={{ .minutes }}" \
  -var 'address_space={{ .address_space }}' \
  -var 'address_prefixes_public={{ .address_prefixes_public }}' \
  -var 'address_prefixes_private={{ .address_prefixes_private }}'

workspace_url=$(terraform output -raw databricks_host)
echo "The link to the workspace is: $workspace_url"
apk update && apk add curl jq

MESSAGE=$(cat <<EOF
The link to the workspace is: ${workspace_url}
The state file can be found here: https://{{ .storage_account_name}}.blob.core.windows.net/{{ .container_name}}
EOF
)

curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "$PAYLOAD"
"""

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a databricks workspace on Azure. Will use IAC (Terraform) to create the workspace. Allows easy, manageable and scalable workspace creation.",
    content=AZURE_WORKSPACE_TEMPLATE,
    args=[
        Arg(name="workspace_name", description="The name of the databricks workspace.", required=True),
        Arg(name="region", description="The azure region for the workspace.", required=True),
        Arg(name="storage_account_name", description="The name of the storage account to use for the backend.", required=True),
        Arg(name="container_name", description="The name of the container to use for the backend.", required=True),
        Arg(name="resource_group_name", description="The name of the resource group to use for the backend.", required=True),
        Arg(name="managed_services_cmk_key_vault_key_id", description="The ID of the key vault key to use for managed services encryption.", required=False),
        Arg(name="managed_disk_cmk_key_vault_key_id", description="The ID of the key vault key to use for managed disk encryption.", required=False),
        Arg(name="infrastructure_encryption_enabled", description="Enable infrastructure encryption, can be true or false.", required=False, default="false"),
        Arg(name="no_public_ip", description="Secure cluster connectivity, no public ip, can be true or false.", required=False, default="false"),
        Arg(name="enable_vnet", description="Enable custom vnet use, boolean, can be true or false.", required=False, default="false"),
        Arg(name="virtual_network_id", description="The virtual network id.", required=False),
        Arg(name="private_subnet_name", description="The name of the private subnet.", required=False),
        Arg(name="public_subnet_name", description="The name of the public subnet.", required=False),
        Arg(name="public_subnet_network_security_group_association_id", description="The ID of the public subnet network security group association.", required=False),
        Arg(name="private_subnet_network_security_group_association_id", description="The ID of the private subnet network security group association.", required=False),
        Arg(name="security_profile_enabled", description="Enable security profile, boolean, can be true or false.", required=False, default="false"),
        Arg(name="enhanced_monitoring_enabled", description="Enable enhanced monitoring, boolean, can be true or false.", required=False, default="false"),
        Arg(name="automatic_update", description="Enable automatic update.", required=False, default="false"),
        Arg(name="restart_no_updates", description="Enable restart even if there are no updates.", required=False, default="false"),
        Arg(name="day_of_week", description="Day of the week to apply updates.", required=False),
        Arg(name="frequency", description="Frequency of updates.", required=False),
        Arg(name="hours", description="Hours of window start time.", required=False, default="1"),
        Arg(name="minutes", description="Minutes of window start time.", required=False, default="0"),
        Arg(name="address_space", description="The address space to be used for the virtual network.", required=False, default='["10.0.0.0/16"]'),
        Arg(name="address_prefixes_public", description="The address prefix for the public network.", required=False, default='["10.0.2.0/24"]'),
        Arg(name="address_prefixes_private", description="The address prefix for the private network.", required=False, default='["10.0.1.0/24"]'),
    ],
    mermaid="""
flowchart TD
    %% User interaction
    User -->|🗨 Request Azure Databricks Workspace| Teammate
    Teammate -->|🗨 Which Resource Group and Location?| User
    User -->|📍 Resource Group: my-rg, Location: eastus| Teammate
    Teammate -->|🚀 Starting Azure Terraform Apply| ApplyAzure

    %% Azure Execution
    subgraph Azure Environment
        ApplyAzure[Azure Kubernetes Job]
        ApplyAzure -->|Running Terraform on Azure 🛠| K8sAzure[Checking Status 🔄]
        K8sAzure -->|⌛ Waiting for Completion| DatabricksAzure[Databricks Workspace Created 🎉]
        ApplyAzure -->|Uses| TerraformDockerAzure[Terraform Docker 🐳]
    end

    %% Feedback to User
    K8sAzure -->|✅ Success! Workspace Ready| Teammate
    Teammate -->|🎉 Workspace is ready!| User
"""
)

tool_registry.register("databricks", azure_db_apply_tool)