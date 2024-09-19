from kubiya_sdk.tools import Arg
from ..base import DatabricksAWSTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import (
    TF_VARS, MERMAID_DIAGRAM, 
    REQUIRED_ENV_VARS, AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING
)
from ..constants import AWS_ENV

# Generate args from TF_VARS
tf_args = [Arg(name=var["name"], description=var["description"], required=var["required"], default=var.get("default")) for var in TF_VARS]

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="create-databricks-workspace-on-aws",
    description="Create a databricks workspace on AWS. Will use IAC (Terraform) to create the workspace. Allows easy, manageable and scalable workspace creation.",
    content=AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    args=tf_args,
    mermaid=MERMAID_DIAGRAM
)

tool_registry.register("databricks", aws_db_apply_tool)

# Ensure all required environment variables are set
for var in REQUIRED_ENV_VARS:
    if var not in AWS_ENV:
        raise ValueError(f"Required environment variable {var} is not set in AWS_ENV")