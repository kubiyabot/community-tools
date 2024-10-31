from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Function to print progress
print_progress() {
    local message="$1"
    local emoji="$2"
    echo -e "\\n${emoji} ${message}" >&2
}

# Function to update status in the main DM thread
update_slack_status() {
    local status="$1"
    local message="$2"
    local phase="$3"
    local plan_output="${4:-}"
    
    # Construct thread URL safely
    local thread_url
    thread_url="https://slack.com/archives/${SLACK_CHANNEL_ID}/p$(echo "$SLACK_THREAD_TS" | tr '.' '')"
    
    # Create JSON payload safely using a temporary file
    local temp_file
    temp_file=$(mktemp)
    
    cat > "$temp_file" << 'EOF'
{
    "channel": "%s",
    "ts": "%s",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "%s",
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
                    "text": "*Phase %s of 4* • Databricks Workspace Deployment"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Workspace:*\n`%s`"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Region:*\n`%s`"
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
                "text": "%s"
            }
        }
EOF

    # Add plan output if available
    if [ -n "$plan_output" ]; then
        cat >> "$temp_file" << 'EOF'
        ,
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Terraform Plan:*\n```%s```"
            }
        }
EOF
    fi

    # Add the view thread button
    cat >> "$temp_file" << 'EOF'
        ,
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
                    "url": "%s"
                }
            ]
        }
    ]
}
EOF

    # Format the JSON with proper values
    local formatted_json
    formatted_json=$(printf "$(cat "$temp_file")" \
        "$SLACK_CHANNEL_ID" \
        "$MAIN_MESSAGE_TS" \
        "$status" \
        "$phase" \
        "{{ .workspace_name }}" \
        "{{ .region }}" \
        "$message" \
        "${plan_output:-}" \
        "$thread_url")

    # Clean up temp file
    rm -f "$temp_file"

    # Send the update to Slack
    curl -s -X POST "https://slack.com/api/chat.update" \
        -H "Authorization: Bearer $SLACK_API_TOKEN" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data "$formatted_json"
}

# Function to handle errors
handle_error() {
    local lineno="$1"
    local errmsg="An unexpected error occurred during the deployment process on line ${lineno}. Please check the logs for more information."
    echo -e "\\n❌ ${errmsg}"
    update_slack_status "❌ Deployment Failed" "$errmsg" "0"
    exit 1
}

# Set error handling
trap 'handle_error $LINENO' ERR

# Function to capture and format Terraform plan
capture_terraform_plan() {
    local plan_output=""
    while IFS= read -r line; do
        echo "$line"  # Print to console
        plan_output="${plan_output}${line}\\n"
    done
    echo "$plan_output"
}

# Start main script execution
print_progress "Starting Databricks Workspace deployment..." "🚀"

# Send initial message to Slack and capture MAIN_MESSAGE_TS
echo -e "📣 Sending initial status message..."
initial_response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $SLACK_API_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data "{
        \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
        \\"text\\": \\"Initializing Databricks Workspace deployment...\\"
    }")

MAIN_MESSAGE_TS=$(echo "$initial_response" | jq -r '.ts')

if [ -z "$MAIN_MESSAGE_TS" ] || [ "$MAIN_MESSAGE_TS" = "null" ]; then
    echo "❌ Failed to send initial message"
    exit 1
fi

# Update initial status
update_slack_status "🚀 Deployment Started" "Initializing Databricks Workspace deployment..." "1"

# Clone repository
print_progress "Cloning Infrastructure Repository..." "📦"
if git clone -b "$BRANCH" "https://$PAT@github.com/$GIT_ORG/$GIT_REPO.git" "$DIR" > /dev/null 2>&1; then
    update_slack_status "📦 Repository Cloned" "Infrastructure repository cloned successfully" "1"
else
    handle_error "Failed to clone repository"
fi

# Initialize Terraform
cd "$DIR/aux/databricks/terraform/azure"
print_progress "Initializing Terraform..." "⚙️"
if terraform init \
    -backend-config="storage_account_name={{ .storage_account_name }}" \
    -backend-config="container_name={{ .container_name }}" \
    -backend-config="key=databricks/{{ .workspace_name }}/terraform.tfstate" \
    -backend-config="resource_group_name={{ .resource_group_name }}" \
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}" > /dev/null; then
    update_slack_status "⚙️ Terraform Initialized" "Terraform successfully initialized" "2"
else
    handle_error "Failed to initialize Terraform"
fi

# Step 3: Apply Terraform configuration
echo -e "\\n🚀 Applying Terraform Configuration..."
print_progress "Generating Terraform plan..." "📋"

# Run terraform plan with real-time output
plan_output=$(terraform plan -var-file="terraform.tfvars.json" 2>&1 | capture_terraform_plan)
plan_exit_code=${PIPESTATUS[0]}

if [ $plan_exit_code -eq 0 ]; then
    print_progress "Terraform plan generated successfully" "✅"
    update_slack_status "🚀 Terraform Plan Generated" "Reviewing changes to be made..." "2" "$plan_output"
    
    print_progress "Applying Terraform configuration..." "🚀"
    terraform apply -auto-approve -var-file="terraform.tfvars.json" 2>&1 | while IFS= read -r line; do
        echo "$line"
        if [[ $line == *"Creating"* ]]; then
            resource=$(echo "$line" | grep -o '"[^"]*"' | head -1)
            [ -n "$resource" ] && update_slack_status "🚀 Deploying Resources" "Creating resource: $resource" "3"
        elif [[ $line == *"Apply complete"* ]]; then
            update_slack_status "✅ Deployment Complete" "All resources have been successfully created" "4"
        fi
    done
    
    apply_exit_code=${PIPESTATUS[0]}
    
    if [ $apply_exit_code -ne 0 ]; then
        handle_error "Failed to apply Terraform configuration"
    fi
else
    handle_error "Failed to generate Terraform plan"
fi

# Get workspace URL
print_progress "Retrieving Databricks Workspace URL..." "🌐"
workspace_url=$(terraform output -raw databricks_host)

if [ -z "$workspace_url" ]; then
    handle_error "Failed to retrieve workspace URL"
fi

workspace_url="https://$workspace_url"
print_progress "Workspace URL: $workspace_url" "🔗"

# Send completion message
print_progress "Deployment completed successfully!" "🎉"
update_slack_status "✅ Deployment Complete" "Databricks workspace *{{ .workspace_name }}* has been successfully provisioned!\\n🌐 *Workspace URL:* $workspace_url" "4"

# Display final timing information
END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
print_progress "Deployment Timing:" "⏱️"
echo "Start Time: $START_TIME" >&2
echo "End Time:   $END_TIME" >&2

# Final success message
update_slack_status "✅ Deployment Successful" "Databricks workspace *{{ .workspace_name }}* has been successfully provisioned!\\n🌐 *Workspace URL:* $workspace_url" "4"

# Record end time
END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "\\n⏰ End Time: $END_TIME"
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