from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_apply_tool = TerraformTool(
    name="terraform_apply",
    description="Applies Terraform changes",
    content="""
    #!/bin/bash
    set -e

    # Change to the module directory if specified
    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    # Initialize Terraform
    terraform init

    # Discover variables if requested
    if [ "$discover_vars" = "true" ]; then
        echo "Discovered variables:"
        terraform show -json | jq -r '.variables | keys[]'
    fi

    # Apply changes
    terraform apply $([[ "$auto_approve" == "true" ]] && echo "-auto-approve") \
                    $([[ -n "$var_file" ]] && echo "-var-file=$var_file") \
                    $([[ -n "$tf_cloud_org" ]] && echo "-backend-config=organization=$tf_cloud_org") \
                    $([[ -n "$tf_cloud_workspace" ]] && echo "-backend-config=workspaces.name=$tf_cloud_workspace")
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module", required=False),
        Arg(name="auto_approve", type="bool", description="Automatically approve and apply changes", required=False),
        Arg(name="var_file", type="str", description="Variable file to use", required=False),
        Arg(name="discover_vars", type="bool", description="Discover and list variables in the module", required=False),
        Arg(name="tf_cloud_org", type="str", description="Terraform Cloud organization", required=False),
        Arg(name="tf_cloud_workspace", type="str", description="Terraform Cloud workspace", required=False),
    ],
)

tool_registry.register("terraform", terraform_apply_tool)