from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash

# Define block templates and helper functions
cat << 'EOF' > /tmp/slack_blocks.json
{
    "init": {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                "alt_text": "github"
            },
            {
                "type": "mrkdwn",
                "text": "*Cloning Infrastructure Repository* • Fetching Terraform configurations"
            }
        ]
    },
    "terraform_init": {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": "https://static-00.iconduck.com/assets.00/terraform-icon-452x512-ildgg5fd.png",
                "alt_text": "terraform"
            },
            {
                "type": "mrkdwn",
                "text": "*Initializing Terraform* • Setting up Azure backend"
            }
        ]
    }
}
EOF

# Constants
SLACK_RATE_LIMIT_DELAY=1.1
MAX_RETRIES=3
RETRY_DELAY=2

# Function to generate progress message
generate_progress_message() {
    local step="$1"
    local status="$2"
    local current_step="$3"
    
    # Get step block from JSON file
    local step_block=$(jq -r ".$step" /tmp/slack_blocks.json)
    
    # Add status icon
    case "$status" in
        "pending") local icon="⊡" ;;
        "in_progress") local icon="🔄" ;;
        "completed") local icon="✅" ;;
        "failed") local icon="❌" ;;
    esac
    
    # Generate full message
    cat << EOF
{
    "blocks": [
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
        },
        {
            "type": "divider"
        },
        $step_block,
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":zap: *Progress:* $current_step of 6 • :stopwatch: *Started:* $START_TIME"
                }
            ]
        }
    ]
}
EOF
}

# Function to update Slack with retry logic
update_slack_progress() {
    local step="$1"
    local status="$2"
    local retry_count=0
    local message
    
    message=$(generate_progress_message "$step" "$status" "$CURRENT_STEP")
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        response=$(curl -s -w "\\n%{http_code}" -X POST "https://slack.com/api/chat.update" \
            -H "Authorization: Bearer $SLACK_API_TOKEN" \
            -H "Content-Type: application/json; charset=utf-8" \
            --data "{
                \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
                \\"ts\\": \\"$MESSAGE_TS\\",
                \\"blocks\\": $message
            }")
        
        http_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "200" ] && [ "$(echo "$response_body" | jq -r '.ok')" = "true" ]; then
            break
        elif [ "$http_code" = "429" ]; then
            sleep "$SLACK_RATE_LIMIT_DELAY"
        else
            retry_count=$((retry_count + 1))
            [ $retry_count -lt $MAX_RETRIES ] && sleep "$RETRY_DELAY"
        fi
    done
}

# Error handling
set -euo pipefail

handle_error() {
    local exit_code=$1
    local error_message="Failed with exit code: $exit_code"
    local error_context=$(tail -n 5 /tmp/terraform.log 2>/dev/null || echo "No log available")
    
    # Update thread message to show failure
    update_slack_progress "$CURRENT_STEP" "failed"
    
    # Send DM about the failure
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
                        \\"text\\": \\"About the Databricks workspace deployment you requested...\\"
                    }
                },
                {
                    \\"type\\": \\"section\\",
                    \\"text\\": {
                        \\"type\\": \\"mrkdwn\\",
                        \\"text\\": \\"I encountered an issue while trying to provision the workspace *{{ .workspace_name }}* in *{{ .region }}*. The deployment failed during the *$(get_current_stage)* stage.\\"
                    }
                },
                {
                    \\"type\\": \\"section\\",
                    \\"text\\": {
                        \\"type\\": \\"mrkdwn\\",
                        \\"text\\": \\"*Error Details:*\\n\`\`\`$error_message\\n$error_context\`\`\`\\"
                    }
                },
                {
                    \\"type\\": \\"section\\",
                    \\"text\\": {
                        \\"type\\": \\"mrkdwn\\",
                        \\"text\\": \\":information_source: *Next Steps:*\\n• Check the detailed logs in the thread above :point_up:\\n• Verify your Azure credentials and permissions\\n• Ensure resource quotas are sufficient\\n• Review network and security configurations\\"
                    }
                },
                {
                    \\"type\\": \\"section\\",
                    \\"text\\": {
                        \\"type\\": \\"mrkdwn\\",
                        \\"text\\": \\"Would you like me to help you troubleshoot this issue or try the deployment again with different parameters?\\"
                    }
                }
            ]
        }"
    
    exit $exit_code
}

trap 'handle_error $?' ERR

# Initialize variables
START_TIME=$(date "+%H:%M:%S")
CURRENT_STEP=1

# Create initial Slack message
MESSAGE_TS=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $SLACK_API_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data "$(generate_progress_message "init" "in_progress" "$CURRENT_STEP")" \
    | jq -r '.ts')

# Setup logging
mkdir -p /tmp/terraform_logs
exec 1> >(tee -a /tmp/terraform_logs/terraform.log)
exec 2>&1

# Clone repository
update_slack_progress "init" "in_progress"
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/azure
update_slack_progress "init" "completed"

# Initialize Terraform
CURRENT_STEP=2
update_slack_progress "terraform_init" "in_progress"
terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name}}" \\
    -backend-config="container_name={{ .container_name}}" \\
    -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name}}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}"
update_slack_progress "terraform_init" "completed"

# Plan Terraform changes
CURRENT_STEP=3
update_slack_progress "terraform_plan" "in_progress"
terraform plan \\
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
    -var "storage_account_name={{ .storage_account_name }}" \\
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
    -var 'address_prefixes_private={{ .address_prefixes_private }}' \\
    -out=tfplan 2>&1 | tee /tmp/terraform_logs/plan.log
update_slack_progress "terraform_plan" "completed"

# Network Configuration
CURRENT_STEP=4
update_slack_progress "network_setup" "in_progress"
if [ "{{ .enable_vnet }}" = "true" ]; then
    echo "Configuring Virtual Network settings..."
    # Network configuration is part of the main apply, but we update status separately
    update_slack_progress "network_setup" "completed"
else
    echo "Skipping Virtual Network configuration..."
    update_slack_progress "network_setup" "completed"
fi

# Security Configuration
CURRENT_STEP=5
update_slack_progress "security_setup" "in_progress"
if [ "{{ .security_profile_enabled }}" = "true" ] || [ "{{ .infrastructure_encryption_enabled }}" = "true" ]; then
    echo "Configuring Security settings..."
    # Security configuration is part of the main apply, but we update status separately
    update_slack_progress "security_setup" "completed"
else
    echo "Skipping advanced security configuration..."
    update_slack_progress "security_setup" "completed"
fi

# Create workspace
CURRENT_STEP=6
update_slack_progress "workspace_setup" "in_progress"
echo "Creating Databricks workspace..."
terraform apply -auto-approve tfplan 2>&1 | tee /tmp/terraform_logs/apply.log

# Verify workspace creation
workspace_url=$(terraform output -raw databricks_host)
if [ -z "$workspace_url" ]; then
    handle_failure "workspace_setup" "Failed to get workspace URL from Terraform output"
fi

workspace_url="https://$workspace_url"

# Verify workspace accessibility
max_retries=10
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl --output /dev/null --silent --head --fail "$workspace_url"; then
        # Final success message
        update_slack_progress "workspace_setup" "completed"
        
        # Send final success message with workspace link
        curl -X POST "https://slack.com/api/chat.postMessage" \\
            -H "Authorization: Bearer $SLACK_API_TOKEN" \\
            -H "Content-Type: application/json; charset=utf-8" \\
            --data "{
                \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
                \\"thread_ts\\": \\"$MESSAGE_TS\\",
                \\"blocks\\": [
                    {
                        \\"type\\": \\"section\\",
                        \\"text\\": {
                            \\"type\\": \\"mrkdwn\\",
                            \\"text\\": \\":tada: *Databricks Workspace Ready!* :rocket:\\n\\nYour workspace has been successfully provisioned and is ready to use.\\"
                        }
                    },
                    {
                        \\"type\\": \\"section\\",
                        \\"text\\": {
                            \\"type\\": \\"mrkdwn\\",
                            \\"text\\": \\"*Workspace URL:* $workspace_url\\"
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
        
        echo "Workspace successfully created and accessible at: $workspace_url"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -eq $max_retries ]; then
            handle_failure "workspace_setup" "Workspace created but not accessible at $workspace_url after $max_retries attempts"
        fi
        echo "Waiting for workspace to become accessible... (attempt $retry_count of $max_retries)"
        sleep 30
    fi
done

# Send DM completion message
curl -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "{
        \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
        \\"blocks\\": [
            {
                \\"type\\": \\"section\\",
                \\"text\\": {
                    \\"type\\": \\"mrkdwn\\",
                    \\"text\\": \\"About the task you asked me to create a Databricks workspace...\\"
                }
            },
            {
                \\"type\\": \\"section\\",
                \\"text\\": {
                    \\"type\\": \\"mrkdwn\\",
                    \\"text\\": \\":white_check_mark: I've successfully provisioned the workspace with the following specifications:\\n\\n• *Workspace Name:* {{ .workspace_name }}\\n• *Region:* {{ .region }}\\n• *VNet Enabled:* {{ .enable_vnet }}\\n• *Security Profile:* {{ .security_profile_enabled }}\\n• *Enhanced Monitoring:* {{ .enhanced_monitoring_enabled }}\\"
                }
            },
            {
                \\"type\\": \\"section\\",
                \\"text\\": {
                    \\"type\\": \\"mrkdwn\\",
                    \\"text\\": \\"You can find the detailed deployment progress in the thread above :point_up: and access your workspace using the button there.\\n\\nIs there anything else you need help with?\\"
                }
            }
        ]
    }"

# Cleanup
rm -f tfplan
rm -f /tmp/slack_blocks.json
rm -rf /tmp/terraform_logs

echo "Deployment completed successfully at $(date "+%H:%M:%S")"
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
        Arg(name="day_of_week", description="Day of the week to apply updates.", required=False),
        Arg(name="frequency", description="Frequency of updates.", required=False),
        Arg(name="hours", description="Hours of window start time.", required=False, default="1"),
        Arg(name="minutes", description="Minutes of window start time.", required=False, default="0"),
        Arg(name="address_space", description="The address space to be used for the virtual network.", required=False, default='["10.0.0.0/16"]'),
        Arg(name="address_prefixes_public", description="The address prefix for the public network.", required=False, default='["10.0.2.0/24"]'),
        Arg(name="address_prefixes_private", description="The address prefix for the private network.", required=False, default='["10.0.1.0/24"]'),
        Arg(name="initial_blocks", description="Initial Slack blocks for progress tracking", required=False, default=INITIAL_SLACK_BLOCKS),
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