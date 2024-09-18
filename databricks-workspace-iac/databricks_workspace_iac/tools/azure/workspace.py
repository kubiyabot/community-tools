from kubiya_sdk.tools import Arg
from ..base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import AZURE_TERRAFORM_DIR, TF_VARS, GIT_CLONE_COMMAND
from ..constants import AZURE_ENV

# Define the template parts
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
""" + "\n".join([f"check_var \"{var}\"" for var in AZURE_ENV]) + """

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
terraform apply -auto-approve """ + " ".join([f"-var {var}" for var in TF_VARS])

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

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a databricks workspace on Azure. Will use IAC (Terraform) to create the workspace. Allows easy, manageable and scalable workspace creation.",
    content=AZURE_WORKSPACE_TEMPLATE,
    args=[
        Arg(name="workspace_name", description="The name of the databricks workspace.", required=True),
        Arg(name="region", description="The azure region for the workspace.", required=True),
        Arg(name="storage_account_name", description="The name of the storage account to use for the backend.", required=True),
        Arg(name="container_name", description="The name of the container to use for the backend.", required=True),
        Arg(name="resource_group_name", description="The name of the resource group to use for the backend.", required=True),
    ],
    env=AZURE_ENV,
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