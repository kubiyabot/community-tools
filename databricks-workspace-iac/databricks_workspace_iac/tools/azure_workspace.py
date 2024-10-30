from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
# Main script starts here

# Set error handling
set -euo pipefail
trap 'handle_error $?' ERR

# Function to handle errors
handle_error() {
    local exit_code="$?"
    echo -e "\\n❌ An error occurred during the deployment process."
    echo -e "🚨 Error on or near line ${BASH_LINENO[0]}: $(sed -n ${BASH_LINENO[0]}p $0)"
    echo -e "💡 Please check the logs for more details."
    exit "$exit_code"
}

# Function to handle failures
handle_failure() {
    local stage="$1"
    local error_message="$2"

    echo -e "\\n❌ Deployment failed during: $stage"
    echo -e "🚨 Error: $error_message"

    # Send failure message to Slack
    curl -s -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data '{
            "channel": "'"$SLACK_CHANNEL_ID"'",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Databricks Workspace Deployment Failed",
                        "emoji": true
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "The deployment failed during *'"$stage"'* stage.\\n*Error Details:*\\n```'"$error_message"'```"
                    }
                }
            ]
        }' > /dev/null

    exit 1
}

echo -e "\\n🔧 Starting Databricks Workspace provisioning on Azure..."

# Record the start time
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ Start Time: $START_TIME"

# Send initial message to Slack
echo -e "\\n📣 Sending initial provisioning message to Slack..."
MESSAGE_TS=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 Databricks Workspace Provisioning Started",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Workspace Name:* `{{ .workspace_name }}`\\n*Region:* `{{ .region }}`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Status:* Cloning the infrastructure repository..."
                }
            }
        ]
    }' | jq -r '.ts')

if [ -z "$MESSAGE_TS" ]; then
    echo -e "❌ Failed to send initial message to Slack."
    exit 1
fi

# Clone the infrastructure repository
echo -e "\\n📥 Cloning infrastructure repository..."
if git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git "$DIR" > /dev/null 2>&1; then
    echo -e "✅ Repository cloned successfully."
else
    handle_failure "Repository Clone" "Failed to clone the repository."
fi

# Update Slack message
echo -e "\\n📣 Updating Slack message: Repository cloned."
curl -s -X POST "https://slack.com/api/chat.update" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "ts": "'"$MESSAGE_TS"'",
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
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Workspace Name:* `{{ .workspace_name }}`\\n*Region:* `{{ .region }}`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Status:* Initializing Terraform..."
                }
            }
        ]
    }' > /dev/null

# Navigate to the Terraform directory
cd "$DIR/aux/databricks/terraform/azure"

# Initialize Terraform
echo -e "\\n🛠 Initializing Terraform..."
if terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name}}" \\
    -backend-config="container_name={{ .container_name}}" \\
    -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name}}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}" > /dev/null; then
    echo -e "✅ Terraform initialized successfully."
else
    handle_failure "Terraform Init" "Failed to initialize Terraform."
fi

# Update Slack message
echo -e "\\n📣 Updating Slack message: Terraform initialized."
curl -s -X POST "https://slack.com/api/chat.update" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "ts": "'"$MESSAGE_TS"'",
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
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Workspace Name:* `{{ .workspace_name }}`\\n*Region:* `{{ .region }}`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Status:* Applying Terraform configuration..."
                }
            }
        ]
    }' > /dev/null

# Apply Terraform configuration
echo -e "\\n🚀 Applying Terraform configuration..."
if terraform apply -auto-approve \\
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
    -var 'address_prefixes_private={{ .address_prefixes_private }}' > /tmp/terraform_apply.log; then
    echo -e "✅ Terraform configuration applied successfully."
else
    error_details=$(cat /tmp/terraform_apply.log)
    handle_failure "Terraform Apply" "$error_details"
fi

# Update Slack message
echo -e "\\n📣 Updating Slack message: Terraform configuration applied."
curl -s -X POST "https://slack.com/api/chat.update" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "ts": "'"$MESSAGE_TS"'",
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
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Workspace Name:* `{{ .workspace_name }}`\\n*Region:* `{{ .region }}`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎉 *Status:* Workspace provisioned successfully!"
                }
            }
        ]
    }' > /dev/null

# Retrieve workspace URL
echo -e "\\n🌐 Retrieving Databricks workspace URL..."
workspace_url=$(terraform output -raw databricks_host)

if [ -z "$workspace_url" ]; then
    handle_failure "Output Retrieval" "Failed to retrieve the workspace URL."
fi
workspace_url="https://$workspace_url"
echo -e "✅ Workspace URL: $workspace_url"

# Send final success message to Slack
echo -e "\\n📣 Sending final success message to Slack..."
curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Databricks Workspace Ready!",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your Databricks workspace has been successfully provisioned!\\n\\n*Workspace URL:* '"$workspace_url"'"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Workspace",
                            "emoji": true
                        },
                        "style": "primary",
                        "url": "'"$workspace_url"'"
                    }
                ]
            }
        ]
    }' > /dev/null

echo -e "\\n🎉 Deployment completed successfully!"
END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ End Time: $END_TIME"

# Send DM to user
echo -e "\\n✉️ Sending confirmation message..."
curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data '{
        "channel": "'"$SLACK_CHANNEL_ID"'",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hey there! :wave:\\n\\nI've successfully completed the provisioning of your Databricks workspace *{{ .workspace_name }}* in the *{{ .region }}* region. You can access your workspace using the link above.\\n\\nIs there anything else I can assist you with?"
                }
            }
        ]
    }' > /dev/null
"""

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a Databricks workspace on Azure using Infrastructure as Code (Terraform).",
    content=AZURE_WORKSPACE_TEMPLATE,
    args=[
        Arg(name="workspace_name", description="The name of the Databricks workspace.", required=True),
        Arg(name="region", description="The Azure region for the workspace.", required=True),
        Arg(name="storage_account_name", description="The name of the storage account to use for the backend.", required=True),
        Arg(name="container_name", description="The name of the container to use for the backend.", required=True),
        Arg(name="resource_group_name", description="The name of the resource group to use for the backend.", required=True),
        Arg(name="managed_services_cmk_key_vault_key_id", description="The ID of the key vault key to use for managed services encryption.", required=False),
        Arg(name="managed_disk_cmk_key_vault_key_id", description="The ID of the key vault key to use for managed disk encryption.", required=False),
        Arg(name="infrastructure_encryption_enabled", description="Enable infrastructure encryption, 'true' or 'false'.", required=False, default="false"),
        Arg(name="no_public_ip", description="Secure cluster connectivity, no public IP, 'true' or 'false'.", required=False, default="false"),
        Arg(name="enable_vnet", description="Enable custom VNet use, 'true' or 'false'.", required=False, default="false"),
        Arg(name="virtual_network_id", description="The virtual network ID.", required=False),
        Arg(name="private_subnet_name", description="The name of the private subnet.", required=False),
        Arg(name="public_subnet_name", description="The name of the public subnet.", required=False),
        Arg(name="public_subnet_network_security_group_association_id", description="The ID of the public subnet NSG association.", required=False),
        Arg(name="private_subnet_network_security_group_association_id", description="The ID of the private subnet NSG association.", required=False),
        Arg(name="security_profile_enabled", description="Enable security profile, 'true' or 'false'.", required=False, default="false"),
        Arg(name="enhanced_monitoring_enabled", description="Enable enhanced monitoring, 'true' or 'false'.", required=False, default="false"),
        Arg(name="automatic_update", description="Enable automatic update, 'true' or 'false'.", required=False, default="false"),
        Arg(name="restart_no_updates", description="Enable restart even if there are no updates, 'true' or 'false'.", required=False, default="false"),
        Arg(name="day_of_week", description="Day of the week to apply updates.", required=False),
        Arg(name="frequency", description="Frequency of updates.", required=False),
        Arg(name="hours", description="Hours of window start time.", required=False, default="1"),
        Arg(name="minutes", description="Minutes of window start time.", required=False, default="0"),
        Arg(name="address_space", description="The address space for the virtual network.", required=False, default='["10.0.0.0/16"]'),
        Arg(name="address_prefixes_public", description="The address prefix for the public network.", required=False, default='["10.0.2.0/24"]'),
        Arg(name="address_prefixes_private", description="The address prefix for the private network.", required=False, default='["10.0.1.0/24"]'),
    ],
    mermaid="""
flowchart TD
    Start[Start Deployment] --> CloneRepo[Clone Repo]
    CloneRepo --> InitTerraform[Initialize Terraform]
    InitTerraform --> ApplyTerraform[Apply Terraform]
    ApplyTerraform --> GetURL[Retrieve Workspace URL]
    GetURL --> SuccessMessage[Send Success Message]
    SuccessMessage --> End[Deployment Complete]
    classDef success fill:#9f6,stroke:#333,stroke-width:2px;
    classDef fail fill:#f66,stroke:#333,stroke-width:2px;
    class CloneRepo,InitTerraform,ApplyTerraform,GetURL,SuccessMessage success;
    class End success;
    class Start success;
"""
)

tool_registry.register("databricks", azure_db_apply_tool)