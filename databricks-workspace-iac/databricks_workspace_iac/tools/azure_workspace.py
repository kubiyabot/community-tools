from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Global variable to store message timestamp
SLACK_MESSAGE_TS=""

# Function to send or update the Slack message
send_slack_message() {
    local blocks="$1"

    if [ -z "${SLACK_MESSAGE_TS}" ]; then
        # Send a new message and capture the timestamp (ts)
        response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \\
            -H "Authorization: Bearer ${SLACK_API_TOKEN}" \\
            -H "Content-Type: application/json; charset=utf-8" \\
            --data '{
                "channel": "'"${SLACK_CHANNEL_ID}"'",
                "blocks": '"${blocks}"'
            }')

        SLACK_MESSAGE_TS=$(echo "$response" | jq -r '.ts')

        if [ -z "${SLACK_MESSAGE_TS}" ] || [ "${SLACK_MESSAGE_TS}" == "null" ]; then
            echo "❌ Failed to send Slack message."
            exit 1
        fi
    else
        # Update the existing message
        curl -s -X POST "https://slack.com/api/chat.update" \\
            -H "Authorization: Bearer ${SLACK_API_TOKEN}" \\
            -H "Content-Type: application/json; charset=utf-8" \\
            --data '{
                "channel": "'"${SLACK_CHANNEL_ID}"'",
                "ts": "'"${SLACK_MESSAGE_TS}"'",
                "blocks": '"${blocks}"'
            }' > /dev/null
    fi
}

# Function to build Slack blocks representing the deployment steps
build_slack_blocks() {
    local current_step="$1"
    local status=("${@:2}")

    # Define the steps
    local steps=("Clone Repository" "Initialize Terraform" "Generate Terraform Plan" "Apply Terraform Configuration" "Retrieve Workspace URL" "Deployment Completed")

    # Initialize blocks
    local blocks='[
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚀 Databricks Workspace Deployment",
            "emoji": true
        }
    },
    {
        "type": "divider"
    }'

    # Add each step to the blocks
    for step in "${steps[@]}"; do
        if [ "$step" == "$current_step" ]; then
            # Highlight the current step
            blocks+=$',\n    {\n        "type": "section",\n        "text": {\n            "type": "mrkdwn",\n            "text": ":arrow_right: *'"$step"'*"\n        }\n    }'
        elif [[ " ${status[@]} " =~ " $step " ]]; then
            # Mark completed steps
            blocks+=$',\n    {\n        "type": "section",\n        "text": {\n            "type": "mrkdwn",\n            "text": ":white_check_mark: ~'"$step"'~"\n        }\n    }'
        else
            # Pending steps
            blocks+=$',\n    {\n        "type": "section",\n        "text": {\n            "type": "mrkdwn",\n            "text": ":black_large_square: '"$step"'\n        }\n    }'
        fi
    done

    blocks+=$'\n]'

    echo "$blocks"
}

# Function to handle errors
handle_error() {
    local lineno="$1"
    local errmsg="$2"
    echo -e "\\n❌ An unexpected error occurred on line ${lineno}: ${errmsg}"
    current_step="Error"
    status+=("$current_step")
    blocks=$(build_slack_blocks "$current_step" "${status[@]}")
    send_slack_message "$blocks"
    exit 1
}

# Trap errors and call handle_error
trap 'handle_error ${LINENO} "${BASH_COMMAND:-command not found}"' ERR

# Initialize status array
status=()

# Main script execution starts here
print_progress "Starting Databricks Workspace deployment..." "🚀"

# Start with the first step
current_step="Clone Repository"
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

# Step 1: Clone Infrastructure Repository
print_progress "Cloning Infrastructure Repository..." "📦"
# ... your cloning logic here ...
# Simulate success
sleep 2
status+=("$current_step")
blocks=$(build_slack_blocks "" "${status[@]}")
send_slack_message "$blocks"

# Step 2: Initialize Terraform
current_step="Initialize Terraform"
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

print_progress "Initializing Terraform..." "⚙️"
# ... your Terraform initialization logic here ...
# Simulate success
sleep 2
status+=("$current_step")
blocks=$(build_slack_blocks "" "${status[@]}")
send_slack_message "$blocks"

# Step 3: Generate Terraform Plan
current_step="Generate Terraform Plan"
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

print_progress "Generating Terraform plan..." "📋"
# ... your Terraform plan generation logic here ...
# Simulate success
sleep 2
status+=("$current_step")
blocks=$(build_slack_blocks "" "${status[@]}")
send_slack_message "$blocks"

# Continue for the rest of the steps...

# Step 4: Apply Terraform Configuration
current_step="Apply Terraform Configuration"
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

print_progress "Applying Terraform configuration..." "🚀"
# ... your Terraform apply logic here ...
# Simulate success
sleep 2
status+=("$current_step")
blocks=$(build_slack_blocks "" "${status[@]}")
send_slack_message "$blocks"

# Step 5: Retrieve Workspace URL
current_step="Retrieve Workspace URL"
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

print_progress "Retrieving Databricks Workspace URL..." "🌐"
# ... your logic to retrieve workspace URL ...
# Simulate success
sleep 2
status+=("$current_step")
blocks=$(build_slack_blocks "" "${status[@]}")
send_slack_message "$blocks"

# Deployment completed
current_step="Deployment Completed"
status+=("$current_step")
blocks=$(build_slack_blocks "$current_step" "${status[@]}")
send_slack_message "$blocks"

print_progress "Deployment completed successfully!" "🎉"

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