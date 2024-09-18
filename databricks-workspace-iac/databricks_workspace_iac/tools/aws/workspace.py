from kubiya_sdk.tools import Arg
from ..base import DatabricksAWSTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import (
    AWS_TERRAFORM_DIR, TF_VARS, GIT_CLONE_COMMAND, 
    MERMAID_DIAGRAM, REQUIRED_ENV_VARS, INIT_TEMPLATE,
    APPLY_TEMPLATE, OUTPUT_TEMPLATE, AWS_WORKSPACE_TEMPLATE
)
from ..constants import AWS_ENV, AWS_FILES

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