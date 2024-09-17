from kubiya_sdk.tools import Arg
from .base import DatabricksAWSTerraformTool
from ..constants import AWS_ENV
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
  -var "WORKSPACE_NAME={{ .workspace_name }}" \
  -var "databricks_client_secret=${DB_ACCOUNT_CLIENT_SECRET}" 

echo "The state file can be found here: https://my-test-backend-bucket.s3.us-west-2.amazonaws.com/aws/"
echo "The databricks workspace can be found here: https://accounts.cloud.databricks.com/workspaces?account_id=${DB_ACCOUNT_ID}"
"""

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="create-databricks-workspace-on-aws",
    description="Create a databricks workspace on AWS.",
    content=AWS_WORKSPACE_TEMPLATE,
    args=[Arg(name="workspace_name", description="The name of the databricks workspace.", required=True)],
    env=AWS_ENV,
    file=AWS_FILES,
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
