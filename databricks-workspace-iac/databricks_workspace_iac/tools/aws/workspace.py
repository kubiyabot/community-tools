from kubiya_sdk.tools import Arg
from ..base import DatabricksAWSTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import AWS_BACKEND_BUCKET, AWS_BACKEND_REGION, AWS_TERRAFORM_DIR, TF_VARS, GIT_CLONE_COMMAND
from ..constants import AWS_ENV, AWS_FILES

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
""" + "\n".join([f"check_var \"{var}\"" for var in AWS_ENV]) + """

echo "✅ All required parameters are set."
"""

INIT_TEMPLATE = f"""
echo "🚀 Initializing Terraform..."
terraform init -backend-config="bucket={AWS_BACKEND_BUCKET}" \
  -backend-config="key=databricks/{{{{ .workspace_name}}}}/terraform.tfstate" \
  -backend-config="region={AWS_BACKEND_REGION}"
"""

APPLY_TEMPLATE = """
echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve """ + " ".join([f"-var {var}" for var in TF_VARS])

OUTPUT_TEMPLATE = """
echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url=${workspace_url:-"https://accounts.cloud.databricks.com/workspaces?account_id=${DB_ACCOUNT_ID}"}

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
                "text": "*To import the state locally, follow these steps:*\n\n1. Configure your Terraform backend:\n\`\`\`\nterraform {\n  backend \"s3\" {\n    $backend_config\n  }\n}\n\`\`\`\n2. Run the import command:\n\`\`\`\nterraform import aws_databricks_workspace.this {{ .workspace_name }}\n\`\`\`"
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
AWS_WORKSPACE_TEMPLATE = f"""
echo "🛠️ Setting up Databricks workspace on AWS..."
{GIT_CLONE_COMMAND}
cd {AWS_TERRAFORM_DIR}

{VALIDATION_TEMPLATE}
{INIT_TEMPLATE}
{APPLY_TEMPLATE}
{OUTPUT_TEMPLATE}
{SLACK_MESSAGE_TEMPLATE}

echo "✅ Databricks workspace setup complete!"
"""

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="create-databricks-workspace-on-aws",
    description="Create a databricks workspace on AWS.",
    content=AWS_WORKSPACE_TEMPLATE,
    args=[
        Arg(name="workspace_name", description="The name of the databricks workspace.", required=True),
    ],
    env=AWS_ENV,
    with_files=AWS_FILES,
    mermaid="""
flowchart TD
    %% User interaction
    User -->|🗨 Request AWS Databricks Workspace| Teammate
    Teammate -->|🗨 What workspace name do you want?| User
    User -->|🏷 Workspace Name: my-workspace| Teammate
    Teammate -->|🚀 Starting AWS Terraform Apply| ApplyAWS

    %% AWS Execution
    subgraph AWS Environment
        ApplyAWS[AWS Kubernetes Job]
        ApplyAWS -->|Running Terraform on AWS 🛠| K8sAWS[Checking Status 🔄]
        K8sAWS -->|⌛ Waiting for Completion| DatabricksAWS[Databricks Workspace Created 🎉]
        ApplyAWS -->|Uses| TerraformDockerAWS[Terraform Docker 🐳]
    end

    %% Feedback to User
    K8sAWS -->|✅ Success! Workspace Ready| Teammate
    Teammate -->|🎉 Workspace is ready!| User
"""
)

tool_registry.register("databricks", aws_db_apply_tool)