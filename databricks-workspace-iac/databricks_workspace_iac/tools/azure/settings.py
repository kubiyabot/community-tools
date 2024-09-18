# Azure-specific settings for Databricks workspace creation

# Directory containing Terraform files for Azure
AZURE_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/azure'

# Function to create Terraform variable dictionaries
def tf_var(name, description, required=False, default=None):
    """
    Create a dictionary representing a Terraform variable.
    
    Args:
        name (str): Name of the variable
        description (str): Description of the variable
        required (bool): Whether the variable is required
        default (Any): Default value for the variable
    
    Returns:
        dict: A dictionary representing the Terraform variable
    """
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default
    }

# Terraform variables
# For more information on these variables, see:
# https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/workspace
TF_VARS = [
    tf_var("workspace_name", "The name of the Databricks workspace to be created", required=True),
    tf_var("region", "The Azure region where the workspace will be deployed", required=True),
    tf_var("storage_account_name", "The name of the storage account to use for the backend", required=True),
    tf_var("container_name", "The name of the container to use for the backend", required=True),
    tf_var("resource_group_name", "The name of the resource group to use for the backend", required=True),
    tf_var("managed_services_cmk_key_vault_key_id", "The ID of the key vault key to use for managed services encryption", required=False),
    tf_var("managed_disk_cmk_key_vault_key_id", "The ID of the key vault key to use for managed disk encryption", required=False),
    tf_var("infrastructure_encryption_enabled", "Enable infrastructure encryption, can be true or false", required=False, default="false"),
    tf_var("no_public_ip", "Secure cluster connectivity, no public ip, can be true or false", required=False, default="false"),
    tf_var("enable_vnet", "Enable custom vnet use, boolean, can be true or false", required=False, default="false"),
    tf_var("virtual_network_id", "The virtual network id", required=False),
    tf_var("private_subnet_name", "The name of the private subnet", required=False),
    tf_var("public_subnet_name", "The name of the public subnet", required=False),
    tf_var("public_subnet_network_security_group_association_id", "The ID of the public subnet network security group association", required=False),
    tf_var("private_subnet_network_security_group_association_id", "The ID of the private subnet network security group association", required=False),
    tf_var("security_profile_enabled", "Enable security profile, boolean, can be true or false", required=False, default="false"),
    tf_var("enhanced_monitoring_enabled", "Enable enhanced monitoring, boolean, can be true or false", required=False, default="false"),
    tf_var("azure_client_id", "Azure client ID", required=False, default="${ARM_CLIENT_ID}"),
    tf_var("azure_client_secret", "Azure client secret", required=False, default="${ARM_CLIENT_SECRET}"),
    tf_var("azure_tenant_id", "Azure tenant ID", required=False, default="${ARM_TENANT_ID}"),
    tf_var("automatic_update", "Enable automatic update", required=False, default="false"),
    tf_var("restart_no_updates", "Enable restart even if there are no updates", required=False, default="false"),
    tf_var("day_of_week", "Day of the week to apply updates", required=False),
    tf_var("frequency", "Frequency of updates", required=False),
    tf_var("hours", "Hours of window start time", required=False, default="1"),
    tf_var("minutes", "Minutes of window start time", required=False, default="0"),
    tf_var("address_space", "The address space to be used for the virtual network", required=False, default='["10.0.0.0/16"]'),
    tf_var("address_prefixes_public", "The address prefix for the public network", required=False, default='["10.0.2.0/24"]'),
    tf_var("address_prefixes_private", "The address prefix for the private network", required=False, default='["10.0.1.0/24"]'),
]

# Git clone command for fetching Terraform configurations
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'

# Mermaid diagram for visualizing the workflow
MERMAID_DIAGRAM = """
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

# Required environment variables for the tool to function
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH", "DIR",
    "ARM_CLIENT_ID", "ARM_CLIENT_SECRET", "ARM_TENANT_ID", "ARM_SUBSCRIPTION_ID",
    "PAT", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "SLACK_API_TOKEN"
]

# Template for validating input parameters
VALIDATION_TEMPLATE = """
echo "🔍 Validating input parameters..."

# Function to check if a variable is set
check_var() {
    if [ -z "$1" ]; then
        echo "❌ Error: $1 is not set. Please provide it as an argument or environment variable."
        exit 1
    fi
}

# Check required variables
""" + "\n".join([f"check_var \"{var}\"" for var in REQUIRED_ENV_VARS]) + """

echo "✅ All required parameters are set."
"""

# Terraform initialization template
INIT_TEMPLATE = """
echo "🚀 Initializing Terraform..."
terraform init -backend-config="storage_account_name={{ .storage_account_name}}" \
  -backend-config="container_name={{ .container_name}}" \
  -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \
  -backend-config="resource_group_name={{ .resource_group_name}}" \
  -backend-config="subscription_id=${ARM_SUBSCRIPTION_ID}"
"""

# Terraform apply template
APPLY_TEMPLATE = """
echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve """ + " ".join([f"-var \"{var['name']}={{{{ .{var['name']} }}}}\"" for var in TF_VARS])

# Output template for capturing and displaying results
OUTPUT_TEMPLATE = """
echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{{}}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url=${workspace_url:-"https://portal.azure.com/#@/resource/subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/{{ .resource_group_name }}/providers/Microsoft.Databricks/workspaces/{{ .workspace_name }}"}

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')
"""

# Template for preparing and sending Slack message
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

# Complete workspace creation template
AZURE_WORKSPACE_TEMPLATE = f"""
echo "🛠️ Setting up Databricks workspace on Azure..."
{GIT_CLONE_COMMAND}
cd {AZURE_TERRAFORM_DIR}

echo "🔍 Validating input parameters..."

# Function to check if a variable is set
check_var() {{
    if [ -z "$1" ]; then
        echo "❌ Error: $1 is not set. Please provide it as an argument or environment variable."
        exit 1
    fi
}}

# Check required variables
{' '.join([f'check_var "${{var}}"' for var in REQUIRED_ENV_VARS])}

echo "✅ All required parameters are set."

echo "🚀 Initializing Terraform..."
terraform init -backend-config="storage_account_name=$storage_account_name" \\
  -backend-config="container_name=$container_name" \\
  -backend-config="key=databricks/$workspace_name/terraform.tfstate" \\
  -backend-config="resource_group_name=$resource_group_name" \\
  -backend-config="subscription_id=$ARM_SUBSCRIPTION_ID"

echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve \\
{' \\\n'.join([f'  -var "{var["name"]}=${{{{ .{var["name"]} | default "{var["default"]}" }}}}"' for var in TF_VARS])}

echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{{}}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url=${{workspace_url:-"https://portal.azure.com/#@/resource/subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/$resource_group_name/providers/Microsoft.Databricks/workspaces/$workspace_name"}}

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')

echo "💬 Preparing Slack message..."
SLACK_MESSAGE=$(cat <<EOF
{{
    "blocks": [
        {{
            "type": "context",
            "elements": [
                {{
                    "type": "image",
                    "image_url": "https://static-00.iconduck.com/assets.00/terraform-icon-1803x2048-hodrzd3t.png",
                    "alt_text": "Terraform Logo"
                }},
                {{
                    "type": "mrkdwn",
                    "text": "🔧 Your *Databricks workspace* was provisioned using *Terraform*, following *Infrastructure as Code (IAC)* best practices for smooth future changes and management. \\n\\n🚀 *Going forward*, you can easily manage and track updates on your infrastructure.\\n\\n🔗 *Module Source code*: <$workspace_url|Explore the module>"
                }}
            ]
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": "*To import the state locally, follow these steps:*\\n\\n1. Configure your Terraform backend:\\n\`\`\`\\nterraform {{\\n  backend \\"azurerm\\" {{\\n    $backend_config\\n  }}\\n}}\\n\`\`\`\\n2. Run the import command:\\n\`\`\`\\nterraform import azurerm_databricks_workspace.this /subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/$resource_group_name/providers/Microsoft.Databricks/workspaces/$workspace_name\\n\`\`\`"
            }}
        }}
    ]
}}
EOF
)

echo "📤 Sending Slack message..."
curl -X POST "https://slack.com/api/chat.postMessage" \\
-H "Authorization: Bearer $SLACK_API_TOKEN" \\
-H "Content-Type: application/json" \\
--data "{{\\"channel\\": \\"$SLACK_CHANNEL_ID\\", \\"thread_ts\\": \\"$SLACK_THREAD_TS\\", \\"blocks\\": $SLACK_MESSAGE}}"

echo "✅ Databricks workspace setup complete!"
"""