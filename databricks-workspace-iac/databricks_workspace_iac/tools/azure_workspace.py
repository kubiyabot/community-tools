from kubiya_sdk.tools import Arg
from .base import DatabricksTerraformTool
from ..constants import AZURE_ENV
from ..models import WorkspaceConfig
from ..utils import generate_terraform_vars, generate_backend_config
from kubiya_sdk.tools.registry import tool_registry

AZURE_WORKSPACE_TEMPLATE = """
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/azure

terraform init {backend_config}
terraform apply -auto-approve \
  -var "azure_client_id=${ARM_CLIENT_ID}" \
  -var "azure_client_secret=${ARM_CLIENT_SECRET}" \
  -var "azure_tenant_id=${ARM_TENANT_ID}" \
  {terraform_vars}

workspace_url=$(terraform output -raw databricks_host)
echo "The link to the workspace is: $workspace_url"
apk update && apk add curl jq

MESSAGE=$(cat <<EOF
The link to the workspace is: ${workspace_url}
The state file can be found here: https://{{ .storage_account_name}}.blob.core.windows.net/{{ .container_name}}
EOF
)
ESCAPED_MESSAGE=$(echo "$MESSAGE" | jq -Rs .)

PAYLOAD=$(cat <<EOF
{{
    "channel": "$SLACK_CHANNEL_ID",
    "text": $ESCAPED_MESSAGE,
    "thread_ts": "$SLACK_THREAD_TS"
}}
EOF
)

curl -X POST "https://slack.com/api/chat.postMessage" \
-H "Authorization: Bearer $SLACK_API_TOKEN" \
-H "Content-Type: application/json" \
--data "$PAYLOAD"
"""

azure_db_apply_tool = DatabricksTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a databricks workspace on Azure. Will use IAC (Terraform) to create the workspace. Allows easy, manageable and scalable workspace creation.",
    content=AZURE_WORKSPACE_TEMPLATE,
    args=[Arg(name=arg, description=arg, required=True) for arg in WorkspaceConfig.__annotations__],
    env=AZURE_ENV
)

tool_registry.register("databricks", azure_db_apply_tool)