from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_workspace_tool = TerraformTool(
    name="terraform_workspace",
    description="Manages Terraform workspaces",
    content="""
    terraform workspace $action $([[ -n "$workspace_name" ]] && echo "$workspace_name")
    """,
    args=[
        Arg(name="action", type="str", description="Workspace action (new, select, list, delete)", required=True),
        Arg(name="workspace_name", type="str", description="Name of the workspace", required=False),
    ],
)

tool_registry.register("terraform", terraform_workspace_tool)