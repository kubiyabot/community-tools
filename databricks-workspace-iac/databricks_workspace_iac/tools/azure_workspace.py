from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash

# Set strict error handling
set -euo pipefail
trap 'handle_error $LINENO' ERR

# Function to handle errors
handle_error() {
    local lineno="$1"
    echo -e "\\n❌ An unexpected error occurred during the deployment process."
    echo -e "🚨 Error on or near line ${lineno}. See the log for details."
    echo -e "💡 Please check the logs for more information.\\n"
    
    # Send failure message to Slack in main channel
    send_slack_failure_message "Deployment" "An unexpected error occurred. Please check the thread for details."
    exit 1
}

# Function to send failure message to Slack in main channel
send_slack_failure_message() {
    local stage="$1"
    local error_message="$2"
    
    echo -e "\\n📣 Sending failure notification to Slack..."
    curl -s -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$(cat << 'EOF'
{
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
                "text": "Unfortunately, the deployment failed during *'"$stage"'* stage.\\n*Error Details:*\\n\`\`\`'"$error_message"'\`\`\`"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "👉 Please check the thread for more details and logs. Let me know if you'd like assistance troubleshooting the issue."
            }
        }
    ]
}
EOF
)" > /dev/null
}

# Function to send messages to Slack thread
send_slack_thread_message() {
    local message="$1"
    local blocks="$2"
    
    curl -s -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$(cat << 'EOF'
{
    "channel": "'"$SLACK_CHANNEL_ID"'",
    "thread_ts": "'"$THREAD_TS"'",
    "text": "'"$message"'",
    "blocks": '"$blocks"'
}
EOF
)" > /dev/null
}

# Function to update the main message in the thread
update_slack_thread_main_message() {
    local blocks="$1"
    
    curl -s -X POST "https://slack.com/api/chat.update" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$(cat << 'EOF'
{
    "channel": "'"$SLACK_CHANNEL_ID"'",
    "ts": "'"$THREAD_TS"'",
    "blocks": '"$blocks"'
}
EOF
)" > /dev/null
}

echo -e "\\n🔧 Let's get started!\\n"
echo -e "✨ Databricks Workspace Provisioning on Azure is about to begin!\\n"

# Record the start time
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ Start Time: $START_TIME\\n"

# Send initial message to Slack and capture THREAD_TS
echo -e "📣 Announcing the start of deployment in Slack...\\n"
initial_response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 Databricks Workspace Deployment Initiated",
                "emoji": true
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Workspace Name:*\n\`{{ .workspace_name }}\`"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Region:*\n\`{{ .region }}\`"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":hourglass_flowing_sand: *Status:* Initialization started..."
            }
        }
    ]
}
EOF
)")

# Capture THREAD_TS
THREAD_TS=$(echo "$initial_response" | jq -r '.ts')
ok=$(echo "$initial_response" | jq -r '.ok')

if [ "$ok" != "true" ] || [ -z "$THREAD_TS" ] || [ "$THREAD_TS" == "null" ]; then
    error=$(echo "$initial_response" | jq -r '.error')
    echo -e "❌ Failed to send initial Slack message: $error\\n"
    exit 1
fi

# Send message to start thread
send_slack_thread_message ":thread: *Deployment Log for Workspace* \`{{ .workspace_name }}\`" "[]"

# Step 1: Clone the infrastructure repository
echo -e "🔍 *Step 1: Cloning Infrastructure Repository...*\\n"
if git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git "$DIR" > /dev/null 2>&1; then
    echo -e "✅ *Repository cloned successfully!*\\n"
    send_slack_thread_message ":white_check_mark: *Step 1 Completed:* Repository cloned successfully." "[]"
else
    handle_failure "Repository Clone" "Failed to clone the repository."
fi

# Update Slack message in thread
update_slack_thread_main_message "$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚀 Databricks Workspace Deployment in Progress",
            "emoji": true
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Workspace Name:*\n\`{{ .workspace_name }}\`"
            },
            {
                "type": "mrkdwn",
                "text": "*Region:*\n\`{{ .region }}\`"
            }
        ]
    },
    {
        "type": "divider"
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":building_construction: *Status:* Terraform initialization started..."
        }
    }
]
EOF
)"

# Step 2: Initialize Terraform
cd "$DIR/aux/databricks/terraform/azure"
echo -e "🔍 *Step 2: Initializing Terraform...*\\n"
if terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name }}" \\
    -backend-config="container_name={{ .container_name }}" \\
    -backend-config="key=databricks/{{ .workspace_name }}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name }}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}" > /dev/null; then
    echo -e "✅ *Terraform initialized successfully!*\\n"
    send_slack_thread_message ":white_check_mark: *Step 2 Completed:* Terraform initialized." "[]"
else
    handle_failure "Terraform Init" "Failed to initialize Terraform."
fi

# Update Slack message in thread
update_slack_thread_main_message "$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚀 Databricks Workspace Deployment in Progress",
            "emoji": true
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Workspace Name:*\n\`{{ .workspace_name }}\`"
            },
            {
                "type": "mrkdwn",
                "text": "*Region:*\n\`{{ .region }}\`"
            }
        ]
    },
    {
        "type": "divider"
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":hammer_and_pick: *Status:* Applying Terraform configuration..."
        }
    }
]
EOF
)"

# Prepare list variables properly by removing the extra quotes
address_space_json={{ .address_space }}
address_prefixes_public_json={{ .address_prefixes_public }}
address_prefixes_private_json={{ .address_prefixes_private }}

# Step 3: Apply Terraform configuration
echo -e "🔍 *Step 3: Applying Terraform Configuration...*\\n"
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
    -var "address_space=${address_space_json}" \\
    -var "address_prefixes_public=${address_prefixes_public_json}" \\
    -var "address_prefixes_private=${address_prefixes_private_json}" \\
    > /tmp/terraform_apply.log; then
    echo -e "✅ *Terraform configuration applied successfully!*\\n"
    send_slack_thread_message ":white_check_mark: *Step 3 Completed:* Terraform configuration applied." "[]"
else
    error_details=$(cat /tmp/terraform_apply.log)
    handle_failure "Terraform Apply" "$error_details"
fi

# Update Slack message in thread
update_slack_thread_main_message "$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚀 Databricks Workspace Deployment in Progress",
            "emoji": true
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Workspace Name:*\n\`{{ .workspace_name }}\`"
            },
            {
                "type": "mrkdwn",
                "text": "*Region:*\n\`{{ .region }}\`"
            }
        ]
    },
    {
        "type": "divider"
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":sparkles: *Status:* Finalizing deployment..."
        }
    }
]
EOF
)"

# Step 4: Retrieve workspace URL
echo -e "🔍 *Step 4: Retrieving Databricks Workspace URL...*\\n"
workspace_url=$(terraform output -raw databricks_host)

if [ -z "$workspace_url" ]; then
    handle_failure "Output Retrieval" "Failed to retrieve the workspace URL."
fi
workspace_url="https://$workspace_url"
echo -e "✅ *Workspace URL:* $workspace_url\\n"

# Send completion message in thread
send_slack_thread_message ":tada: *Deployment Completed Successfully!* :tada:" "[]"

# Update main message to reflect completion
update_slack_thread_main_message "$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "✅ Databricks Workspace Deployment Successful",
            "emoji": true
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Workspace Name:*\n\`{{ .workspace_name }}\`"
            },
            {
                "type": "mrkdwn",
                "text": "*Region:*\n\`{{ .region }}\`"
            }
        ]
    },
    {
        "type": "divider"
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":star: *Status:* Deployment completed successfully!"
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Workspace URL:* $workspace_url"
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
                "url": "$workspace_url"
            }
        ]
    }
]
EOF
)"

# Send success message in main channel
echo -e "📣 Announcing success in Slack...\\n"
curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "text": "Hey there! :wave: Your Databricks workspace *{{ .workspace_name }}* in region *{{ .region }}* has been successfully provisioned! Check out the details in the thread.",
    "thread_ts": null
}
EOF
)" > /dev/null

echo -e "🎉 Deployment completed successfully!\\n"

END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ End Time: $END_TIME\\n"

# Additional message in main channel offering assistance
echo -e "✉️ Sending a final message in Slack...\\n"
curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "text": "If there's anything else I can assist you with, feel free to let me know! :smile:",
    "thread_ts": null
}
EOF
)" > /dev/null
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
        Arg(
            name="address_space",
            description="The address space for the virtual network.",
            required=False,
            default='["10.0.0.0/16"]'
        ),
        Arg(
            name="address_prefixes_public",
            description="The address prefix for the public network.",
            required=False,
            default='["10.0.2.0/24"]'
        ),
        Arg(
            name="address_prefixes_private",
            description="The address prefix for the private network.",
            required=False,
            default='["10.0.1.0/24"]'
        ),
    ],
    mermaid="""
flowchart TD
    Start[Start Deployment] --> Step1[Clone Repo]
    Step1 --> Step2[Initialize Terraform]
    Step2 --> Step3[Apply Terraform]
    Step3 --> Step4[Retrieve Workspace URL]
    Step4 --> Success[Deployment Successful]
    classDef success fill:#9f6,stroke:#333,stroke-width:2px;
    classDef fail fill:#f66,stroke:#333,stroke-width:2px;
    class Start,Step1,Step2,Step3,Step4,Success success;
"""
)

tool_registry.register("databricks", azure_db_apply_tool)