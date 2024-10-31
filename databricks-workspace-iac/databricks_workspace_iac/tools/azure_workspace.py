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
    send_slack_message "❌ Deployment Failed" "${errmsg}"
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

# Function to send Slack message to the thread
send_slack_message() {
    local status="$1"
    local message="$2"
    local plan_output="${3:-}"

    # Ensure SLACK_THREAD_TS is set
    if [ -z "${SLACK_THREAD_TS:-}" ]; then
        echo "❌ SLACK_THREAD_TS environment variable is not set."
        exit 1
    fi

    # Construct thread URL safely
    local thread_url="https://slack.com/archives/${SLACK_CHANNEL_ID}/p${SLACK_THREAD_TS//./}"

    # Create the JSON payload for the thread message
    local thread_payload
    thread_payload=$(cat <<EOF
{
    "channel": "${SLACK_CHANNEL_ID}",
    "thread_ts": "${SLACK_THREAD_TS}",
    "mrkdwn": true,
    "text": "${status}\\n${message}"
}
EOF
)

    # If plan output is provided, include it in the message
    if [ -n "${plan_output}" ]; then
        thread_payload=$(cat <<EOF
{
    "channel": "${SLACK_CHANNEL_ID}",
    "thread_ts": "${SLACK_THREAD_TS}",
    "mrkdwn": true,
    "text": "${status}\\n${message}\\n\\n*Terraform Plan:*\\n\`\`\`${plan_output}\`\`\`"
}
EOF
)
    fi

    # Send the message to the thread
    curl -s -X POST "https://slack.com/api/chat.postMessage" \\
        -H "Authorization: Bearer ${SLACK_API_TOKEN}" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "${thread_payload}" > /dev/null
}

# Main script execution starts here
print_progress "Starting Databricks Workspace deployment..." "🚀"

# Ensure required environment variables are set
if [ -z "${SLACK_API_TOKEN:-}" ] || [ -z "${SLACK_CHANNEL_ID:-}" ] || [ -z "${SLACK_THREAD_TS:-}" ]; then
    echo "❌ Required environment variables SLACK_API_TOKEN, SLACK_CHANNEL_ID, or SLACK_THREAD_TS are not set."
    exit 1
fi

# Proceed with deployment steps

# Example of sending a message to the thread
send_slack_message "🚀 Deployment Started" "Initializing Databricks Workspace deployment..."

# Step 1: Clone Infrastructure Repository
print_progress "Cloning Infrastructure Repository..." "📦"
send_slack_message "📦 Cloning Repository" "Cloning the infrastructure repository..."

# ... your cloning logic here ...

# Step 2: Initialize Terraform
print_progress "Initializing Terraform..." "⚙️"
send_slack_message "⚙️ Initializing Terraform" "Initializing Terraform configuration..."

# ... your Terraform initialization logic here ...

# Step 3: Generate Terraform Plan
print_progress "Generating Terraform plan..." "📋"
send_slack_message "📋 Generating Terraform Plan" "Generating Terraform plan..."

# Capture Terraform plan output
plan_output=$(terraform plan -no-color -input=false -var-file="terraform.tfvars.json")

# Check if plan was successful
if [ $? -eq 0 ]; then
    print_progress "Terraform plan generated successfully" "✅"
    send_slack_message "✅ Terraform Plan Generated" "Terraform plan generated successfully." "${plan_output}"
else
    error_message="Failed to generate Terraform plan"
    print_progress "${error_message}" "❌"
    send_slack_message "❌ ${error_message}" "Please check the logs for details."
    exit 1
fi

# Step 4: Apply Terraform Configuration
print_progress "Applying Terraform configuration..." "🚀"
send_slack_message "🚀 Applying Terraform Configuration" "Applying Terraform configuration..."

# Apply the Terraform configuration
apply_output=$(terraform apply -auto-approve -no-color -input=false -var-file="terraform.tfvars.json")

# Check if apply was successful
if [ $? -eq 0 ]; then
    print_progress "Terraform configuration applied successfully!" "🎉"
    send_slack_message "🎉 Deployment Successful" "Terraform configuration applied successfully!"
else
    error_message="Failed to apply Terraform configuration"
    print_progress "${error_message}" "❌"
    send_slack_message "❌ ${error_message}" "Please check the logs for details."
    exit 1
fi

# Step 5: Retrieve Workspace URL
print_progress "Retrieving Databricks Workspace URL..." "🌐"
workspace_url=$(terraform output -raw databricks_host)

if [ -z "${workspace_url}" ]; then
    handle_error ${LINENO} "Failed to retrieve workspace URL"
fi

workspace_url="https://${workspace_url}"
print_progress "Workspace URL: ${workspace_url}" "🔗"
send_slack_message "🔗 Workspace URL" "Databricks Workspace is available at: ${workspace_url}"

# Deployment completed
print_progress "Deployment completed successfully!" "🎉"
send_slack_message "🎉 Deployment Completed" "Databricks Workspace deployment completed successfully!"

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