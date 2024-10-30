from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

INITIAL_SLACK_BLOCKS = """
{
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 Databricks Workspace Provisioning",
                "emoji": true
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://azure.microsoft.com/favicon.ico",
                    "alt_text": "azure"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Azure Region:* \`{{ .region }}\`"
                },
                {
                    "type": "image",
                    "image_url": "https://cdn-icons-png.flaticon.com/512/2885/2885417.png",
                    "alt_text": "workspace"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Workspace:* \`{{ .workspace_name }}\`"
                }
            ]
        }
    ]
}
"""

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Function to update Slack message
update_slack_message() {
    local status="$1"
    local blocks="$2"
    
    curl -X POST "https://slack.com/api/chat.update" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "{
        \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
        \\"ts\\": \\"$MESSAGE_TS\\",
        \\"blocks\\": $blocks
    }"
}

# Function to handle failures
handle_failure() {
    local stage="$1"
    local error_message="$2"
    
    curl -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "{
        \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
        \\"blocks\\": [
            {
                \\"type\\": \\"header\\",
                \\"text\\": {
                    \\"type\\": \\"plain_text\\",
                    \\"text\\": \\"❌ Databricks Workspace Deployment Failed\\",
                    \\"emoji\\": true
                }
            },
            {
                \\"type\\": \\"section\\",
                \\"text\\": {
                    \\"type\\": \\"mrkdwn\\",
                    \\"text\\": \\"Failed during: $stage\\n\`\`\`$error_message\`\`\`\\"
                }
            }
        ]
    }"
    exit 1
}

trap 'handle_error $?' ERR

# Send initial message
MESSAGE_TS=$(curl -X POST "https://slack.com/api/chat.postMessage" \\
-H "Authorization: Bearer $SLACK_API_TOKEN" \\
-H "Content-Type: application/json; charset=utf-8" \\
--data "$(echo '$INITIAL_SLACK_BLOCKS' | sed "s/{{ .workspace_name }}/{{ .workspace_name }}/g" | sed "s/{{ .region }}/{{ .region }}/g")" \\
| jq -r '.ts')

# Clone repository
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/azure

# Initialize Terraform
terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name}}" \\
    -backend-config="container_name={{ .container_name}}" \\
    -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name}}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}"

# Apply Terraform configuration
terraform apply -auto-approve \\
    -var "workspace_name={{ .workspace_name }}" \\
    -var "region={{ .region }}" \\
    -var "managed_services_cmk_key_vault_key_id={{ .managed_services_cmk_key_vault_key_id }}" \\
    -var "managed_disk_cmk_key_vault_key_id={{ .managed_disk_cmk_key_vault_key_id }}" \\
    -var "infrastructure_encryption_enabled={{ .infrastructure_encryption_enabled }}" \\
    -var "no_public_ip={{ .no_public_ip }}" \\
    -var "enable_vnet={{ .enable_vnet }}" \\
    -var "virtual_network_id={{ .virtual_network_id }}" \\
    -var "private_subnet_name={{ .private_subnet_name }}" \\
    -var "public_subnet_name={{ .public_subnet_name }}" \\
    -var "public_subnet_network_security_group_association_id={{ .public_subnet_network_security_group_association_id }}" \\
    -var "private_subnet_network_security_group_association_id={{ .private_subnet_network_security_group_association_id }}" \\
    -var "security_profile_enabled={{ .security_profile_enabled }}" \\
    -var "enhanced_monitoring_enabled={{ .enhanced_monitoring_enabled }}" \\
    -var "automatic_update={{ .automatic_update }}" \\
    -var "restart_no_updates={{ .restart_no_updates }}" \\
    -var "day_of_week={{ .day_of_week }}" \\
    -var "frequency={{ .frequency }}" \\
    -var "hours={{ .hours }}" \\
    -var "minutes={{ .minutes }}" \\
    -var 'address_space={{ .address_space }}' \\
    -var 'address_prefixes_public={{ .address_prefixes_public }}' \\
    -var 'address_prefixes_private={{ .address_prefixes_private }}'

workspace_url=$(terraform output -raw databricks_host)
workspace_url="https://$workspace_url"

# Send success message
curl -X POST "https://slack.com/api/chat.postMessage" \\
-H "Authorization: Bearer $SLACK_API_TOKEN" \\
-H "Content-Type: application/json; charset=utf-8" \\
--data "{
    \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
    \\"blocks\\": [
        {
            \\"type\\": \\"header\\",
            \\"text\\": {
                \\"type\\": \\"plain_text\\",
                \\"text\\": \\"✅ Databricks Workspace Ready!\\",
                \\"emoji\\": true
            }
        },
        {
            \\"type\\": \\"section\\",
            \\"text\\": {
                \\"type\\": \\"mrkdwn\\",
                \\"text\\": \\"Your workspace has been successfully provisioned at:\\n$workspace_url\\"
            }
        },
        {
            \\"type\\": \\"actions\\",
            \\"elements\\": [
                {
                    \\"type\\": \\"button\\",
                    \\"text\\": {
                        \\"type\\": \\"plain_text\\",
                        \\"text\\": \\"Open Workspace\\",
                        \\"emoji\\": true
                    },
                    \\"style\\": \\"primary\\",
                    \\"url\\": \\"$workspace_url\\"
                }
            ]
        }
    ]
}"
"""

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a databricks workspace on Azure using Infrastructure as Code (Terraform).",
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
        Arg(name="day_of_week", description="Day of the week to apply updates.", required="false"),
        Arg(name="frequency", description="Frequency of updates.", required=False),
        Arg(name="hours", description="Hours of window start time.", required=False, default="1"),
        Arg(name="minutes", description="Minutes of window start time.", required=False, default="0"),
        Arg(name="address_space", description="The address space to be used for the virtual network.", required=False, default='["10.0.0.0/16"]'),
        Arg(name="address_prefixes_public", description="The address prefix for the public network.", required=False, default='["10.0.2.0/24"]'),
        Arg(name="address_prefixes_private", description="The address prefix for the private network.", required=False, default='["10.0.1.0/24"]')
    ],
    mermaid="""
    flowchart TD
        %% User Interaction Flow
        User -->|🗨️ Request Azure Databricks Workspace| Teammate
        Teammate -->|📋 Request Workspace Details| User
        User -->|💼 Provide Configuration| Teammate
        
        %% Configuration Details
        subgraph Configuration Details 🔧
            WorkspaceConfig[Workspace Settings]
            NetworkConfig[Network Settings]
            SecurityConfig[Security Settings]
            
            WorkspaceConfig -->|Name & Region| ConfigValidation
            NetworkConfig -->|VNET & Subnets| ConfigValidation
            SecurityConfig -->|Encryption & Access| ConfigValidation
        end

        %% Terraform Execution Flow
        subgraph Terraform Pipeline 🛠️
            ConfigValidation[Validate Config ✔️]
            TerraformInit[terraform init 🔄]
            TerraformPlan[terraform plan 📋]
            TerraformApply[terraform apply 🚀]
            
            ConfigValidation -->|Valid| TerraformInit
            TerraformInit -->|Success| TerraformPlan
            TerraformPlan -->|Approved| TerraformApply
        end

        %% Azure Resource Creation
        subgraph Azure Resources 🏢
            ResourceGroup[Resource Group]
            VNET[Virtual Network]
            Subnets[Public/Private Subnets]
            NSG[Network Security Groups]
            KeyVault[Key Vault]
            DatabricksWorkspace[Databricks Workspace]
            
            ResourceGroup -->|Contains| VNET
            VNET -->|Configured with| Subnets
            Subnets -->|Secured by| NSG
            KeyVault -->|Encrypts| DatabricksWorkspace
        end

        %% Dynamic Variables
        subgraph Variables 📝
            direction LR
            Vars1[workspace_name]
            Vars2[region]
            Vars3[storage_account]
            Vars4[vnet_config]
            Vars5[security_settings]
        end

        %% Status Updates
        TerraformApply -->|Creating Resources ⚙️| Azure Resources
        Azure Resources -->|Provisioning| Status[Status Check 🔍]
        Status -->|Success ✅| Complete[Workspace Ready! 🎉]
        
        %% Final Notification
        Complete -->|Workspace URL & Access Details| Teammate
        Teammate -->|🎯 Workspace Ready for Use!| User

        %% Styling
        classDef configNode fill:#f9f,stroke:#333,stroke-width:2px
        classDef terraformNode fill:#bbf,stroke:#333,stroke-width:2px
        classDef azureNode fill:#bfb,stroke:#333,stroke-width:2px
        
        class WorkspaceConfig,NetworkConfig,SecurityConfig configNode
        class TerraformInit,TerraformPlan,TerraformApply terraformNode
        class ResourceGroup,VNET,DatabricksWorkspace azureNode
    """
)

tool_registry.register("databricks", azure_db_apply_tool)