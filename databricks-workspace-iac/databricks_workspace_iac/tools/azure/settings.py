# Azure-specific settings
AZURE_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/azure'

# Define a function to create Terraform variable strings
def tf_var(name, description, required=False, default=None):
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default
    }

# Terraform variables
TF_VARS = [
    tf_var("workspace_name", "The name of the Databricks workspace to be created", required=True),
    tf_var("region", "The Azure region where the workspace will be deployed", required=True),
    tf_var("storage_account_name", "The name of the storage account to use for the backend", required=True),
    tf_var("container_name", "The name of the container to use for the backend", required=True),
    tf_var("resource_group_name", "The name of the resource group to use for the backend", required=True),
    tf_var("managed_services_cmk_key_vault_key_id", "The ID of the key vault key to use for managed services encryption"),
    tf_var("managed_disk_cmk_key_vault_key_id", "The ID of the key vault key to use for managed disk encryption"),
    tf_var("infrastructure_encryption_enabled", "Enable infrastructure encryption, can be true or false", default=False),
    tf_var("no_public_ip", "Secure cluster connectivity, no public ip, can be true or false", default=False),
    tf_var("enable_vnet", "Enable custom vnet use, boolean, can be true or false", default=False),
    tf_var("virtual_network_id", "The virtual network id"),
    tf_var("private_subnet_name", "The name of the private subnet"),
    tf_var("public_subnet_name", "The name of the public subnet"),
    tf_var("public_subnet_network_security_group_association_id", "The ID of the public subnet network security group association"),
    tf_var("private_subnet_network_security_group_association_id", "The ID of the private subnet network security group association"),
    tf_var("security_profile_enabled", "Enable security profile, boolean, can be true or false", default=False),
    tf_var("enhanced_monitoring_enabled", "Enable enhanced monitoring, boolean, can be true or false", default=False),
    tf_var("azure_client_id", "Azure client ID", default="${ARM_CLIENT_ID}"),
    tf_var("azure_client_secret", "Azure client secret", default="${ARM_CLIENT_SECRET}"),
    tf_var("azure_tenant_id", "Azure tenant ID", default="${ARM_TENANT_ID}"),
    tf_var("automatic_update", "Enable automatic update", default=False),
    tf_var("restart_no_updates", "Enable restart even if there are no updates", default=False),
    tf_var("day_of_week", "Day of the week to apply updates"),
    tf_var("frequency", "Frequency of updates"),
    tf_var("hours", "Hours of window start time", default="1"),
    tf_var("minutes", "Minutes of window start time", default="0"),
    tf_var("address_space", "The address space to be used for the virtual network", default='["10.0.0.0/16"]'),
    tf_var("address_prefixes_public", "The address prefix for the public network", default='["10.0.2.0/24"]'),
    tf_var("address_prefixes_private", "The address prefix for the private network", default='["10.0.1.0/24"]'),
]

# Git clone command
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'

# Mermaid diagram
MERMAID_DIAGRAM = """
graph LR
    A[Start] --> B[Clone Repository]
    B --> C[Initialize Terraform]
    C --> D[Apply Terraform]
    D --> E[Capture Output]
    E --> F[Send Slack Message]
    F --> G[End]
"""

# Required environment variables
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH", "DIR",
    "ARM_CLIENT_ID", "ARM_CLIENT_SECRET", "ARM_TENANT_ID", "ARM_SUBSCRIPTION_ID",
    "PAT", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "SLACK_API_TOKEN"
]

# Template parts
VALIDATION_TEMPLATE = """
echo "🔍 Validating input parameters..."

# Function to check if a variable is set
check_var() {
    if [ -z "${!1}" ]; then
        echo "❌ Error: $1 is not set. Please provide it as an argument or environment variable."
        exit 1
    fi
}

# Check required variables
""" + "\n".join([f"check_var \"{var}\"" for var in REQUIRED_ENV_VARS]) + """

echo "✅ All required parameters are set."
"""

INIT_TEMPLATE = """
echo "🚀 Initializing Terraform..."
terraform init -backend-config="storage_account_name={{ .storage_account_name}}" \
  -backend-config="container_name={{ .container_name}}" \
  -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \
  -backend-config="resource_group_name={{ .resource_group_name}}" \
  -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}"
"""

APPLY_TEMPLATE = """
echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve """ + " ".join([f"-var \"{var['name']}={{{{ .{var['name']} }}}}\"" for var in TF_VARS])

OUTPUT_TEMPLATE = """
echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url=${workspace_url:-"https://portal.azure.com/#@/resource/subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/{{ .resource_group_name }}/providers/Microsoft.Databricks/workspaces/{{ .workspace_name }}"}

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')
"""

SLACK_MESSAGE_TEMPLATE = """
echo "💬 Preparing Slack message..."
SLACK_MESSAGE=$(cat <<EOF
{
    "blocks": [
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://static-00.iconduck.com/assets.00/terraform-icon-1803x2048-hodrzd3t.png",
                    "alt_text": "Terraform Logo"
                },
                {
                    "type": "mrkdwn",
                    "text": "🔧 Your *Databricks workspace* was provisioned using *Terraform*, following *Infrastructure as Code (IAC)* best practices for smooth future changes and management. \n\n🚀 *Going forward*, you can easily manage and track updates on your infrastructure.\n\n🔗 *Module Source code*: <$workspace_url|Explore the module>"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*To import the state locally, follow these steps:*\n\n1. Configure your Terraform backend:\n\`\`\`\nterraform {\n  backend \"azurerm\" {\n    $backend_config\n  }\n}\n\`\`\`\n2. Run the import command:\n\`\`\`\nterraform import azurerm_databricks_workspace.this /subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/{{ .resource_group_name }}/providers/Microsoft.Databricks/workspaces/{{ .workspace_name }}\n\`\`\`"
            }
        }
    ]
}
EOF
)

echo "📤 Sending Slack message..."
curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "{\"channel\": \"$SLACK_CHANNEL_ID\", \"thread_ts\": \"$SLACK_THREAD_TS\", \"blocks\": $SLACK_MESSAGE}"
"""

# Build the content template
AZURE_WORKSPACE_TEMPLATE = f"""
echo "🛠️ Setting up Databricks workspace on Azure..."
{GIT_CLONE_COMMAND}
cd {AZURE_TERRAFORM_DIR}

{VALIDATION_TEMPLATE}
{INIT_TEMPLATE}
{APPLY_TEMPLATE}
{OUTPUT_TEMPLATE}
{SLACK_MESSAGE_TEMPLATE}

echo "✅ Databricks workspace setup complete!"
"""