from typing import Annotated, Optional
from kubiya_sdk.tools import function_tool
import typer

@function_tool(
    description="Create a Databricks workspace on AWS using Infrastructure as Code (Terraform).",
    requirements=["slack_sdk>=3.19.0"],
    long_running=True,
    icon_url="https://raw.githubusercontent.com/databricks/databricks-sdk-py/main/docs/_static/databricks-icon.png"
)
def create_databricks_workspace_aws(
    # AWS specific parameters here
) -> str:
    """Create a Databricks workspace on AWS using Infrastructure as Code (Terraform)."""
    # Implementation here
    pass
