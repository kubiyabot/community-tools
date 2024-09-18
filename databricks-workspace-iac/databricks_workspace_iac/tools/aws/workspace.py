from kubiya_sdk.tools import Arg
from ..base import DatabricksAWSTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import (
    AWS_BACKEND_BUCKET, AWS_BACKEND_REGION, AWS_TERRAFORM_DIR, TF_VARS, 
    GIT_CLONE_COMMAND, MERMAID_DIAGRAM, REQUIRED_ENV_VARS
)
from ..constants import AWS_ENV, AWS_FILES

# Define the template parts
INIT_TEMPLATE = f"""
echo "🚀 Initializing Terraform..."
terraform init -backend-config="bucket={AWS_BACKEND_BUCKET}" \
  -backend-config="key=databricks/{{{{ .workspace_name}}}}/terraform.tfstate" \
  -backend-config="region={AWS_BACKEND_REGION}"
"""

APPLY_TEMPLATE = """
echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve """ + " ".join([f"-var \"{var['name']}=${{{var['default']}}}\"" if var['default'] else f"-var \"{var['name']}={{{{ .{var['name']} }}}}\"" for var in TF_VARS])

OUTPUT_TEMPLATE = f"""
echo "The state file can be found here: https://{AWS_BACKEND_BUCKET}.s3.{AWS_BACKEND_REGION}.amazonaws.com/aws/"
echo "The databricks workspace can be found here: https://accounts.cloud.databricks.com/workspaces?account_id=${{DB_ACCOUNT_ID}}"
"""

# Build the content template
AWS_WORKSPACE_TEMPLATE = f"""
echo "🛠️ Setting up Databricks workspace on AWS..."
{GIT_CLONE_COMMAND}
cd {AWS_TERRAFORM_DIR}

{INIT_TEMPLATE}
{APPLY_TEMPLATE}
{OUTPUT_TEMPLATE}

echo "✅ Databricks workspace setup complete!"
"""

# Generate args from TF_VARS
tf_args = [Arg(name=var["name"], description=var["description"], required=var["required"], default=var.get("default")) for var in TF_VARS]

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="aws-db-apply-tool",
    description="Create a databricks workspace on AWS.",
    content=AWS_WORKSPACE_TEMPLATE,
    args=tf_args,
    mermaid=MERMAID_DIAGRAM
)

tool_registry.register("databricks", aws_db_apply_tool)

# Ensure all required environment variables are set
for var in REQUIRED_ENV_VARS:
    if var not in AWS_ENV:
        raise ValueError(f"Required environment variable {var} is not set in AWS_ENV")