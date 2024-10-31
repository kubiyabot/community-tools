from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Function to handle errors
handle_error() {
    local lineno="$1"
    local errmsg="$2"
    echo -e "\\n❌ An unexpected error occurred on line ${lineno}: ${errmsg}"
    update_slack_status "❌ Deployment Failed" "${errmsg}" "0"
    exit 1
}

# Trap errors and call handle_error
trap 'handle_error ${LINENO} "$BASH_COMMAND"' ERR

# Function to print progress
print_progress() {
    local message="$1"
    local emoji="$2"
    echo -e "\\n${emoji} ${message}"
}

# Function to update Slack status in both the main thread and the parent message
update_slack_status() {
    local status="$1"
    local message="$2"
    local phase="$3"
    local plan_output="${4:-}"

    # Ensure SLACK_THREAD_TS is set
    if [ -z "${SLACK_THREAD_TS:-}" ]; then
        echo "❌ SLACK_THREAD_TS environment variable is not set."
        exit 1
    fi

    # Use SLACK_THREAD_TS as the thread timestamp
    THREAD_TS="${SLACK_THREAD_TS}"

    # Construct thread URL safely
    local thread_url="https://slack.com/archives/${SLACK_CHANNEL_ID}/p${THREAD_TS//./}"

    # Create the JSON payload for the main thread
    local thread_payload
    thread_payload=$(cat <<EOF
{
    "channel": "${SLACK_CHANNEL_ID}",
    "ts": "${THREAD_TS}",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "${status}",
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
                    "text": "*Phase ${phase} of 4* • Databricks Workspace Deployment"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Workspace:*\n\`{{ .workspace_name }}\`"
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
                "text": "${message}"
            }
        }$(if [ -n "${plan_output}" ]; then
cat <<EOP
,
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Terraform Plan:*\n\`\`\`${plan_output}\`\`\`"
            }
        }
EOP
fi)
    ]
}
EOF
)

    # Create the JSON payload for the parent message (includes the View Thread button)
    local parent_payload
    parent_payload=$(cat <<EOF
{
    "channel": "${SLACK_CHANNEL_ID}",
    "ts": "${SLACK_MESSAGE_TS}",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "${status}",
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
                    "text": "*Phase ${phase} of 4* • Databricks Workspace Deployment"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Workspace:*\n\`{{ .workspace_name }}\`"
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
                "text": "${message}\n\n_This is a long-running operation. Updates will be posted here and in the thread for easy reference._"
            }
        }$(if [ -n "${plan_output}" ]; then
cat <<EOP
,
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Terraform Plan:*\n\`\`\`${plan_output}\`\`\`"
            }
        }
EOP
fi),
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
                    "url": "${thread_url}"
                }
            ]
        }
    ]
}
EOF
)

    # Update the main thread message
    curl -s -X POST "https://slack.com/api/chat.update" \
        -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data "${thread_payload}" > /dev/null

    # Update the parent message
    curl -s -X POST "https://slack.com/api/chat.update" \
        -H "Authorization: Bearer ${SLACK_API_TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data "${parent_payload}" > /dev/null
}

# Main script execution starts here
print_progress "Starting Databricks Workspace deployment..." "🚀"

# Ensure required environment variables are set
if [ -z "${SLACK_API_TOKEN:-}" ] || [ -z "${SLACK_CHANNEL_ID:-}" ] || [ -z "${SLACK_THREAD_TS:-}" ] || [ -z "${SLACK_MESSAGE_TS:-}" ]; then
    echo "❌ Required environment variables SLACK_API_TOKEN, SLACK_CHANNEL_ID, SLACK_THREAD_TS, or SLACK_MESSAGE_TS are not set."
    exit 1
fi

# Use SLACK_THREAD_TS as the thread timestamp
THREAD_TS="${SLACK_THREAD_TS}"

# Proceed with deployment steps

# Example of updating the status
update_slack_status "🚀 Deployment Started" "Initializing Databricks Workspace deployment..." "1"

# Rest of your script...
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