from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_output_tool = TerraformTool(
    name="terraform_output",
    description="Reads an output from a Terraform state file",
    content="""
    terraform output $([[ -n "$output_name" ]] && echo "$output_name") $([[ "$json" == "true" ]] && echo "-json")
    """,
    args=[
        Arg(name="output_name", type="str", description="Name of the output to read", required=False),
        Arg(name="json", type="bool", description="Print output in JSON format", required=False),
    ],
)

tool_registry.register("terraform", terraform_output_tool)