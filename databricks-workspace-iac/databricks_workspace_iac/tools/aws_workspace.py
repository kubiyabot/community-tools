from kubiya_sdk.tools import Arg
from .base import DatabricksAWSTerraformTool
from ..constants import AWS_ENV
from ..models import WorkspaceConfig
from ..utils import generate_terraform_vars
from kubiya_sdk.tools.registry import tool_registry

AWS_WORKSPACE_TEMPLATE = """
git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR
cd $DIR/aux/databricks/terraform/aws  

terraform init -backend-config="bucket=my-test-backend-bucket" \
  -backend-config="key=databricks/{{ .workspace_name}}/terraform.tfstate" \
  -backend-config="region=us-west-2"
terraform apply -auto-approve \
  -var "databricks_account_id=${DB_ACCOUNT_ID}" \
  -var "databricks_client_id=${DB_ACCOUNT_CLIENT_ID}" \
  -var "databricks_client_secret=${DB_ACCOUNT_CLIENT_SECRET}" \
  {terraform_vars}

echo "The state file can be found here: https://my-test-backend-bucket.s3.us-west-2.amazonaws.com/aws/"
echo "The databricks workspace can be found here: https://accounts.cloud.databricks.com/workspaces?account_id=${DB_ACCOUNT_ID}"
"""

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="aws-db-apply-tool",
    description="Create a databricks workspace on AWS.",
    content=AWS_WORKSPACE_TEMPLATE,
    args=[Arg(name=arg, description=arg, required=True) for arg in WorkspaceConfig.__annotations__],
    env=AWS_ENV
)

tool_registry.register("databricks", aws_db_apply_tool)
