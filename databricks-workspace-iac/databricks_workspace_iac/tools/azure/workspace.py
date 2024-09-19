from kubiya_sdk.tools import Arg
from ..base import DatabricksAzureTerraformTool
from kubiya_sdk.tools.registry import tool_registry
from .settings import (
    TF_VARS, MERMAID_DIAGRAM, 
    REQUIRED_ENV_VARS, AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING
)
from ..constants import AZURE_ENV

# Generate args from TF_VARS
tf_args = [Arg(name=var["name"], description=var["description"], required=var["required"], default=var.get("default")) for var in TF_VARS]

azure_db_apply_tool = DatabricksAzureTerraformTool(
    name="create-databricks-workspace-on-azure",
    description="Create a databricks workspace on Azure. Will use IAC (Terraform) to create the workspace. Allows easy, manageable and scalable workspace creation.",
    content=AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    args=tf_args,
    mermaid=MERMAID_DIAGRAM
)

tool_registry.register("databricks", azure_db_apply_tool)

# Ensure all required environment variables are set
for var in REQUIRED_ENV_VARS:
    if var not in AZURE_ENV:
        raise ValueError(f"Required environment variable {var} is not set in AZURE_ENV")