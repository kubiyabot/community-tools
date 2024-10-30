from kubiya_sdk.tools import Arg
from .base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
#!/bin/bash
set -euo pipefail

# Function to handle errors and update Slack messages
handle_error() {
    local lineno="$1"
    local errmsg="An unexpected error occurred during the deployment process on line ${lineno}. Please check the logs for more information."
    echo -e "\\n❌ ${errmsg}"
    update_slack_status ":x: Deployment Failed" "$errmsg"
    exit 1
}

# Set error handling
trap 'handle_error $LINENO' ERR

# Function to update status in the main DM thread
update_slack_status() {
    local status="$1"
    local message="$2"
    
    # Construct thread URL using the original thread timestamp
    local thread_url="https://slack.com/archives/${SLACK_CHANNEL_ID}/p${SLACK_THREAD_TS//.}"
    
    curl -s -X POST "https://slack.com/api/chat.update" \\
        -H "Authorization: Bearer $SLACK_API_TOKEN" \\
        -H "Content-Type: application/json; charset=utf-8" \\
        --data "{
            \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
            \\"ts\\": \\"$MAIN_MESSAGE_TS\\",
            \\"blocks\\": [
                {
                    \\"type\\": \\"section\\",
                    \\"text\\": {
                        \\"type\\": \\"mrkdwn\\",
                        \\"text\\": \\"$status\\n$message\\"
                    }
                },
                {
                    \\"type\\": \\"actions\\",
                    \\"elements\\": [
                        {
                            \\"type\\": \\"button\\",
                            \\"text\\": {
                                \\"type\\": \\"plain_text\\",
                                \\"text\\": \\"View Thread\\",
                                \\"emoji\\": true
                            },
                            \\"url\\": \\"$thread_url\\"
                        }
                    ]
                }
            ]
        }" > /dev/null
}

# Function to update deployment status
update_deployment_status() {
    local phase="$1"
    local message="$2"
    
    echo -e "\\n📢 $message"
    update_slack_status "🚀 Phase $phase" "$message"
}

# Main deployment process
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

echo -e "\\n🔧 Let's get started!\\n"
echo -e "✨ Databricks Workspace Provisioning on Azure is about to begin!\\n"

# Record the start time
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "⏰ Start Time: $START_TIME\\n"

# Send initial message and capture its timestamp
echo -e "📣 Sending initial status message..."
initial_response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \\
    -H "Authorization: Bearer $SLACK_API_TOKEN" \\
    -H "Content-Type: application/json; charset=utf-8" \\
    --data "{
        \\"channel\\": \\"$SLACK_CHANNEL_ID\\",
        \\"text\\": \\"Initializing Databricks Workspace deployment...\\"
    }")

# Capture the timestamp of the message we'll be updating
MAIN_MESSAGE_TS=$(echo "$initial_response" | jq -r '.ts')

if [ -z "$MAIN_MESSAGE_TS" ] || [ "$MAIN_MESSAGE_TS" = "null" ]; then
    echo "❌ Failed to send initial message"
    exit 1
fi

# Now we can start updating the status
update_deployment_status "1/4" "Initializing Databricks Workspace deployment for {{ .workspace_name }} in {{ .region }}\\n_This is a long-running operation, you can follow the progress in the thread._"

# Step 1: Clone the infrastructure repository
echo -e "\\n🔍 Cloning Infrastructure Repository..."
if [ -z "$BRANCH" ] || [ -z "$PAT" ] || [ -z "$GIT_ORG" ] || [ -z "$GIT_REPO" ] || [ -z "$DIR" ]; then
    handle_error "Required git variables are not set (BRANCH, PAT, GIT_ORG, GIT_REPO, or DIR)"
fi

clone_output=$(git clone -b "$BRANCH" "https://$PAT@github.com/$GIT_ORG/$GIT_REPO.git" "$DIR" 2>&1)
clone_status=$?

if [ $clone_status -eq 0 ]; then
    update_deployment_status "2/4" "✅ Repository cloned successfully"
else
    handle_error "Failed to clone repository: $clone_output"
fi

# Step 2: Initialize Terraform
cd "$DIR/aux/databricks/terraform/azure"
echo -e "\\n🔧 Initializing Terraform..."
if terraform init \\
    -backend-config="storage_account_name={{ .storage_account_name }}" \\
    -backend-config="container_name={{ .container_name }}" \\
    -backend-config="key=databricks/{{ .workspace_name }}/terraform.tfstate" \\
    -backend-config="resource_group_name={{ .resource_group_name }}" \\
    -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}" > /dev/null; then
    update_deployment_status "3/4" "✅ Terraform initialized successfully"
else
    handle_error "Failed to initialize Terraform"
fi

# Step 3: Apply Terraform configuration
echo -e "\\n🚀 Applying Terraform Configuration..."
update_deployment_status "3/4" "Applying Terraform configuration (this may take several minutes)..."

# Create terraform vars file to avoid command line length issues
cat > terraform.tfvars.json <<'EOF'
{
    "workspace_name": "{{ .workspace_name }}",
    "region": "{{ .region }}"
    {{- if .managed_services_cmk_key_vault_key_id }},
    "managed_services_cmk_key_vault_key_id": "{{ .managed_services_cmk_key_vault_key_id }}"
    {{- end }}
    {{- if .managed_disk_cmk_key_vault_key_id }},
    "managed_disk_cmk_key_vault_key_id": "{{ .managed_disk_cmk_key_vault_key_id }}"
    {{- end }},
    "infrastructure_encryption_enabled": {{ if eq .infrastructure_encryption_enabled "true" }}true{{ else }}false{{ end }},
    "no_public_ip": {{ if eq .no_public_ip "true" }}true{{ else }}false{{ end }},
    "enable_vnet": {{ if eq .enable_vnet "true" }}true{{ else }}false{{ end }}
    {{- if .virtual_network_id }},
    "virtual_network_id": "{{ .virtual_network_id }}"
    {{- end }}
    {{- if .private_subnet_name }},
    "private_subnet_name": "{{ .private_subnet_name }}"
    {{- end }}
    {{- if .public_subnet_name }},
    "public_subnet_name": "{{ .public_subnet_name }}"
    {{- end }}
    {{- if .public_subnet_network_security_group_association_id }},
    "public_subnet_network_security_group_association_id": "{{ .public_subnet_network_security_group_association_id }}"
    {{- end }}
    {{- if .private_subnet_network_security_group_association_id }},
    "private_subnet_network_security_group_association_id": "{{ .private_subnet_network_security_group_association_id }}"
    {{- end }},
    "security_profile_enabled": {{ if eq .security_profile_enabled "true" }}true{{ else }}false{{ end }},
    "enhanced_monitoring_enabled": {{ if eq .enhanced_monitoring_enabled "true" }}true{{ else }}false{{ end }},
    "automatic_update": {{ if eq .automatic_update "true" }}true{{ else }}false{{ end }},
    "restart_no_updates": {{ if eq .restart_no_updates "true" }}true{{ else }}false{{ end }}
    {{- if .day_of_week }},
    "day_of_week": "{{ .day_of_week }}"
    {{- end }}
    {{- if .frequency }},
    "frequency": "{{ .frequency }}"
    {{- end }}
    {{- if ne .hours "1" }},
    "hours": "{{ .hours }}"
    {{- end }}
    {{- if ne .minutes "0" }},
    "minutes": "{{ .minutes }}"
    {{- end }}
    {{- if .address_space }},
    "address_space": {{ .address_space }}
    {{- end }}
    {{- if .address_prefixes_public }},
    "address_prefixes_public": {{ .address_prefixes_public }}
    {{- end }}
    {{- if .address_prefixes_private }},
    "address_prefixes_private": {{ .address_prefixes_private }}
    {{- end }}
}
EOF

# Debug: Show the generated JSON
echo "Generated terraform.tfvars.json content:"
cat terraform.tfvars.json

# Verify the JSON file is valid
if ! jq '.' terraform.tfvars.json > /dev/null 2>&1; then
    handle_error "Invalid JSON in terraform.tfvars.json: $(cat terraform.tfvars.json)"
fi

# Apply Terraform configuration using vars file
if terraform apply -auto-approve -var-file="terraform.tfvars.json" > /tmp/terraform_apply.log 2>&1; then
    update_deployment_status "4/4" "✅ Terraform configuration applied successfully"
else
    error_details=$(cat /tmp/terraform_apply.log)
    handle_error "Failed to apply Terraform configuration: $error_details"
fi

# Step 4: Retrieve and display workspace URL
echo -e "\\n🌐 Retrieving Databricks Workspace URL..."
workspace_url=$(terraform output -raw databricks_host)

if [ -z "$workspace_url" ]; then
    handle_error "Failed to retrieve workspace URL"
fi

workspace_url="https://$workspace_url"
echo -e "\\n✅ Deployment completed successfully!"
echo -e "🌐 Workspace URL: $workspace_url"

# Final success message
update_slack_status "✅ Deployment Successful" "Databricks workspace *{{ .workspace_name }}* has been successfully provisioned!\\n🌐 *Workspace URL:* $workspace_url"

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