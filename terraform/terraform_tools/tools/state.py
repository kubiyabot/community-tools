from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_state_tool = TerraformTool(
    name="terraform_state",
    description="Advanced state management",
    content="""
    terraform state $action $([[ -n "$address" ]] && echo "$address")
    """,
    args=[
        Arg(name="action", type="str", description="State action (list, mv, pull, push, rm, show)", required=True),
        Arg(name="address", type="str", description="Resource address", required=False),
    ],
)

tool_registry.register("terraform", terraform_state_tool)