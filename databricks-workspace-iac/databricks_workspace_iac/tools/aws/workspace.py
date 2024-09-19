# aws/workspace.py

from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from databricks_workspace_iac.tools.base import DatabricksAWSTerraformTool
from databricks_workspace_iac.tools.aws.settings import (
    TF_VARS, MERMAID_DIAGRAM,
    REQUIRED_ENV_VARS, AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING
)

# Generate args from TF_VARS
tf_args = [
    Arg(
        name=var["name"],
        description=var["description"],
        required=var["required"],
        default=var.get("default")
    ) for var in TF_VARS
]

aws_db_apply_tool = DatabricksAWSTerraformTool(
    name="create-databricks-workspace-on-aws",
    description="Create a Databricks workspace on AWS using Terraform for IAC.",
    content=AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    args=tf_args,
    env=REQUIRED_ENV_VARS,
    mermaid=MERMAID_DIAGRAM
)

tool_registry.register("databricks", aws_db_apply_tool)
