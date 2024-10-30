from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Friendly message with emoji
echo -e "\\n🔧 Starting the setup for Databricks Workspace provisioning..."

# Check and install runtime dependencies silently
check_dependencies() {
    missing_deps=""
    for cmd in curl jq git bash; do
        if ! command -v "$cmd" > /dev/null 2>&1; then
            missing_deps="$missing_deps $cmd"
        fi
    done

    if [ -n "$missing_deps" ]; then
        echo -e "⚙️  This workflow requires additional dependencies which haven't been cached yet."
        echo -e "🚀 Installing missing dependencies: $missing_deps"
        if apk update > /dev/null 2>&1 && apk add --no-cache $missing_deps > /dev/null 2>&1; then
            echo -e "✅ Dependencies installed successfully!"
        else
            echo -e "❌ Failed to install dependencies: $missing_deps"
            exit 1
        fi
    else
        echo -e "✅ All dependencies are already installed!"
    fi
}

# Ensure dependencies are installed
check_dependencies

# Set strict error handling
set -euo pipefail
trap 'handle_error $LINENO' ERR

# Function to handle errors and update Slack messages
handle_error() {
    local lineno="$1"
    local errmsg="An unexpected error occurred during the deployment process on line ${lineno}. Please check the logs for more information."

    echo -e "\\n❌ ${errmsg}"
    update_slack_main_message ":x: Deployment Failed" "$errmsg" "An error occurred during deployment. See details in the thread."
    send_slack_thread_message ":x: *Error:* ${errmsg}" "[]"
    exit 1
}

# Function to send messages to Slack thread
send_slack_thread_message() {
    local message="$1"
    local blocks="$2"

    echo -e "\\n📤 Sending update to Slack thread: $message"

    curl -s -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "thread_ts": "$THREAD_TS",
    "text": "$message",
    "blocks": $blocks
}
EOF
    )" > /dev/null
}

# Function to update the main message in the thread
update_slack_main_message() {
    local status="$1"
    local summary="$2"
    local context="$3"

    local blocks="$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "$status",
            "emoji": true
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Workspace Name:*\\n\`{{ .workspace_name }}\`"
            },
            {
                "type": "mrkdwn",
                "text": "*Region:*\\n\`{{ .region }}\`"
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
            "text": "$summary"
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "$context"
            }
        ]
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Thread",
                    "emoji": true
                },
                "url": "$THREAD_URL"
            }
        ]
    }
]
EOF
    )"

    curl -s -X POST "https://slack.com/api/chat.update" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "ts": "$MAIN_MESSAGE_TS",
    "blocks": $blocks
}
EOF
    )" > /dev/null
}

# Function to send progress updates
send_progress_update() {
    local phase="$1"
    local total_phases="$2"
    local status_icon="$3"
    local status_message="$4"
    local eta="$5"

    echo -e "\\n${status_icon} ${status_message}"

    local blocks="$(cat <<EOF
[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚀 Databricks Workspace Deployment",
            "emoji": true
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": "https://static-00.iconduck.com/assets.00/terraform-icon-452x512-ildgg5fd.png",
                "alt_text": "terraform"
            },
            {
                "type": "mrkdwn",
                "text": "*Provisioning Infrastructure* • Phase ${phase} of ${total_phases}"
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
            "text": "${status_icon} ${status_message}"
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":zap: *Phase ${phase} of ${total_phases}* • :stopwatch: *ETA:* ${eta} minutes"
            }
        ]
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "_Note: This task might take up to ${eta} minutes depending on Terraform apply against the providers involved._"
            }
        ]
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Thread",
                    "emoji": true
                },
                "url": "$THREAD_URL"
            }
        ]
    }
]
EOF
    )"

    update_slack_main_message "🚀 Deployment In Progress" "${status_message}" "Currently in phase ${phase} of ${total_phases}."
}

echo -e "\\n🔧 Let's get started!\\n"
echo -e "✨ Databricks Workspace Provisioning on Azure is about to begin!\\n"

# Record the start time
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ Start Time: $START_TIME\\n"

# Send initial message to Slack and capture MAIN_MESSAGE_TS
echo -e "📣 Announcing the start of deployment in Slack...\\n"
initial_response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "text": "🚀 *Deployment Initiated for Workspace* \`{{ .workspace_name }}\`",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚀 *Deployment Initiated for Workspace* \`{{ .workspace_name }}\` in region \`{{ .region }}\`.\n\n_Long running operation in progress, I will keep you updated on any progress._"
            }
        }
    ]
}
EOF
    )")

# Capture MAIN_MESSAGE_TS and build THREAD_URL
MAIN_MESSAGE_TS=$(echo "$initial_response" | jq -r '.ts')
ok=$(echo "$initial_response" | jq -r '.ok')

if [ "$ok" != "true" ] || [ -z "$MAIN_MESSAGE_TS" ] || [ "$MAIN_MESSAGE_TS" == "null" ]; then
    error=$(echo "$initial_response" | jq -r '.error')
    echo -e "❌ Failed to send initial Slack message: $error\\n"
    exit 1
fi

# Use MAIN_MESSAGE_TS as THREAD_TS
THREAD_TS="$MAIN_MESSAGE_TS"

# Build THREAD_URL safely by encoding THREAD_TS
THREAD_TS_ENCODED=$(echo "$THREAD_TS" | sed 's/\\./%2E/g')
THREAD_URL="https://yourdomain.slack.com/archives/${SLACK_CHANNEL_ID}/p${THREAD_TS_ENCODED}"

# Update the initial message to include the "View Thread" button now that THREAD_URL is available
update_initial_message_blocks="$(cat <<EOF
[
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "🚀 *Deployment Initiated for Workspace* \`{{ .workspace_name }}\` in region \`{{ .region }}\`.\n\n_Long running operation in progress, I will keep you updated on any progress._"
        }
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Thread",
                    "emoji": true
                },
                "url": "$THREAD_URL"
            }
        ]
    }
]
EOF
)"

# Update the initial message with the "View Thread" button
curl -s -X POST "https://slack.com/api/chat.update" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "ts": "$MAIN_MESSAGE_TS",
    "blocks": $update_initial_message_blocks
}
EOF
    )" > /dev/null

# Send message to start thread
send_slack_thread_message ":thread: *Deployment Log for Workspace* \`{{ .workspace_name }}\`" "[]"

# Step 1: Clone the infrastructure repository
echo -e "\\n🔍 *Step 1: Cloning Infrastructure Repository...*"
send_progress_update "1" "4" "🔍" "Cloning Infrastructure Repository..." "10"

if git clone -b "$BRANCH" "https://$PAT@$GIT_ORG/$GIT_REPO.git" "$DIR" > /dev/null 2>&1; then
    echo -e "✅ *Repository cloned successfully!*"
    send_slack_thread_message "✅ *Step 1 Completed:* Repository cloned successfully." "[]"
else
    handle_error
fi

# Step 2: Initialize Terraform
echo -e "\\n🔧 *Step 2: Initializing Terraform...*"
send_progress_update "2" "4" "🔧" "Initializing Terraform..." "8"

cd "$DIR/aux/databricks/terraform/azure"

if terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name }}" \\
    -backend-config="container_name={{ .container_name }}" \\
    -backend-config="key=databricks/{{ .workspace_name }}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name }}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}" > /dev/null; then
    echo -e "✅ *Terraform initialized successfully!*"
    send_slack_thread_message "✅ *Step 2 Completed:* Terraform initialized." "[]"
else
    handle_error
fi

# Step 3: Apply Terraform configuration
echo -e "\\n🚜 *Step 3: Applying Terraform Configuration...*"
send_progress_update "3" "4" "🚜" "Applying Terraform Configuration..." "5"

# Prepare list variables properly
address_space_json={{ .address_space }}
address_prefixes_public_json={{ .address_prefixes_public }}
address_prefixes_private_json={{ .address_prefixes_private }}

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
    > /tmp/terraform_apply.log 2>&1; then
    echo -e "✅ *Terraform configuration applied successfully!*"
    send_slack_thread_message "✅ *Step 3 Completed:* Terraform configuration applied." "[]"
else
    error_details=$(cat /tmp/terraform_apply.log)
    send_slack_thread_message ":x: *Error during Terraform Apply:*" "[]"
    send_slack_thread_message "```$error_details```" "[]"
    handle_error
fi

# Step 4: Retrieve workspace URL
echo -e "\\n🌐 *Step 4: Retrieving Databricks Workspace URL...*"
send_progress_update "4" "4" "🌐" "Retrieving Workspace URL..." "1"

workspace_url=$(terraform output -raw databricks_host)

if [ -z "$workspace_url" ]; then
    handle_error
fi
workspace_url="https://$workspace_url"
echo -e "✅ *Workspace URL:* $workspace_url"

# Send completion message in thread
send_slack_thread_message ":tada: *Deployment Completed Successfully!* :tada:" "[]"

# Update main message to reflect completion with button to open workspace
update_slack_main_message "✅ Deployment Successful" "*Workspace URL:* $workspace_url" "Deployment completed successfully!"

# Announce success in Slack main channel with button to view thread
curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "ts": "$MAIN_MESSAGE_TS",
    "text": "🎉 Deployment of *{{ .workspace_name }}* completed successfully!",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🎉 Deployment of *{{ .workspace_name }}* in region *{{ .region }}* completed successfully!\n\n_You can access the workspace or view the deployment thread for more details._"
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
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Deployment Thread",
                        "emoji": true
                    },
                    "url": "$THREAD_URL"
                }
            ]
        }
    ]
}
EOF
    )" > /dev/null

echo -e "\\n🎉 Deployment completed successfully!"
echo -e "⏰ End Time: $(date "+%Y-%m-%d %H:%M:%S")\\n"
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