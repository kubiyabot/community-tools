from kubiya_sdk.tools import Arg
from .base import DatabricksAWSTerraformTool
from kubiya_sdk.tools.registry import tool_registry

AWS_WORKSPACE_TEMPLATE = """
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/aws  

terraform init -backend-config="bucket={{ .backend_bucket }}" \
  -backend-config="key=databricks/{{ .workspace_name }}/terraform.tfstate" \
  -backend-config="region={{ .backend_region }}"
terraform apply -auto-approve \
  -var "databricks_account_id=${DB_ACCOUNT_ID}" \
  -var "databricks_client_id=${DB_ACCOUNT_CLIENT_ID}" \
  -var "workspace_name={{ .workspace_name }}" \
  -var "databricks_client_secret=${DB_ACCOUNT_CLIENT_SECRET}" \
  -var "aws_region={{ .aws_region }}" \
  -var "enable_vpc={{ .enable_vpc }}" \
  -var "vpc_id={{ .vpc_id }}" \
  -var "enable_privatelink={{ .enable_privatelink }}" \
  -var "enable_cmk={{ .enable_cmk }}" 

workspace_url=$(terraform output -raw databricks_host)
echo "The link to the workspace is: $workspace_url"

# Install required packages
apk update && apk add curl jq

# Prepare the message
MESSAGE=$(cat <<EOF
The link to the workspace is: ${workspace_url}
EOF
)
ESCAPED_MESSAGE=$(echo "$MESSAGE" | jq -Rs .)

# Check for required environment variables
if [ -z "$SLACK_CHANNEL_ID" ] || [ -z "$SLACK_THREAD_TS" ] || [ -z "$SLACK_API_TOKEN" ]; then
  echo "Error: SLACK_CHANNEL_ID, SLACK_THREAD_TS, and SLACK_API_TOKEN must be set."
  exit 1
fi

# Prepare the payload for sending a multiline message in a thread
PAYLOAD=$(cat <<EOF
{
    "channel": "$SLACK_CHANNEL_ID",
    "text": $ESCAPED_MESSAGE,
    "thread_ts": "$SLACK_THREAD_TS"
}
EOF
)

# Send the message using Slack API
curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "$PAYLOAD"
"""

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="create-databricks-workspace-on-aws",
    description="Create a databricks workspace on AWS.",
    content=AWS_WORKSPACE_TEMPLATE,
    args=[
        Arg(name="workspace_name", description="The name of the databricks workspace.", required=True),
        Arg(name="aws_region", description="The AWS region for the Databricks workspace.", required=True),
        Arg(name="backend_bucket", description="The S3 bucket to use for Terraform state backend.", required=True),
        Arg(name="backend_region", description="The AWS region for the Terraform state backend.", required=True),
        Arg(name="enable_vpc", description="Optional: Enable VPC creation (true/false).", required=False, default="True"),
        Arg(name="vpc_id", description="Optional: Existing VPC ID to use for the workspace.", required=False, default=""),
        Arg(name="enable_privatelink", description="Advanced: Enable AWS PrivateLink for the Databricks workspace.", required=False, default="False"),
        Arg(name="enable_cmk", description="Advanced: Enable Customer Managed Keys for the Databricks workspace.", required=False, default="False"),
    ],
    mermaid="""
    // ... existing mermaid diagram ...
    """
)

tool_registry.register("databricks", aws_db_apply_tool)
