from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_workflow_tool = TerraformTool(
    name="terraform_workflow",
    description="Executes a complete Terraform workflow",
    content="""
    # Initialize
    terraform init $([[ -n "$backend_config" ]] && echo "-backend-config=$backend_config")

    # Plan
    terraform plan -out=tfplan $([[ -n "$var_file" ]] && echo "-var-file=$var_file")

    # Apply if auto_approve is set
    if [ "$auto_approve" = "true" ]; then
        terraform apply -auto-approve tfplan
    else
        echo "Plan created. Run 'terraform apply tfplan' to apply changes."
    fi

    # Output if show_output is set
    if [ "$show_output" = "true" ]; then
        terraform output
    fi
    """,
    args=[
        Arg(name="backend_config", type="str", description="Backend configuration file", required=False),
        Arg(name="var_file", type="str", description="Variable file", required=False),
        Arg(name="auto_approve", type="bool", description="Automatically approve and apply changes", required=False),
        Arg(name="show_output", type="bool", description="Show output after apply", required=False),
    ],
)

tool_registry.register("terraform", terraform_workflow_tool)