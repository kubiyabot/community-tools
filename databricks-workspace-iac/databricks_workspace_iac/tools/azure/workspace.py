# azure/workspace.py

from kubiya_sdk.tools import Arg
from tools.base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from tools.azure.settings import (
    TF_VARS,
    MERMAID_DIAGRAM,
    REQUIRED_ENV_VARS,
    AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    REQUIRED_SECRETS,
)

# Generate args from TF_VARS
tf_args = [
    Arg(
        name=var["name"],
        description=var["description"],
        required=var["required"],
        default=var.get("default"),
    )
    for var in TF_VARS
    if var["default"] is not None
]

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a Databricks workspace on Azure using Terraform for IAC. Allows flexible configuration of Terraform variables using a smooth English conversation - no Terraform knowledge required.",
    content=AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    args=tf_args,
    env=REQUIRED_ENV_VARS,
    mermaid=MERMAID_DIAGRAM,
    secrets=REQUIRED_SECRETS,
)

tool_registry.register("databricks", azure_db_apply_tool)
