from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_destroy_tool = TerraformTool(
    name="terraform_destroy",
    description="Destroys Terraform-managed infrastructure",
    content="""
    terraform destroy $([[ "$auto_approve" == "true" ]] && echo "-auto-approve") $([[ -n "$var_file" ]] && echo "-var-file=$var_file")
    """,
    args=[
        Arg(name="auto_approve", type="bool", description="Automatically approve and destroy", required=False),
        Arg(name="var_file", type="str", description="Variable file to use", required=False),
    ],
)

tool_registry.register("terraform", terraform_destroy_tool)