from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_module_tool = TerraformTool(
    name="terraform_module",
    description="Manages Terraform modules",
    content="""
    case $action in
        get)
            terraform get -update
            ;;
        use)
            if [ -n "$module_source" ]; then
                echo "module \"$module_name\" {" > main.tf
                echo "  source = \"$module_source\"" >> main.tf
                echo "}" >> main.tf
                terraform init
            else
                echo "Module source is required for 'use' action"
                exit 1
            fi
            ;;
        list)
            terraform show -json | jq '.module_calls'
            ;;
        discover_vars)
            if [ -n "$module_path" ]; then
                cd "$module_path"
            fi
            terraform init
            echo "Discovered variables:"
            terraform show -json | jq -r '.variables | keys[]'
            ;;
        *)
            echo "Invalid action. Use 'get', 'use', 'list', or 'discover_vars'."
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Module action (get, use, list, discover_vars)", required=True),
        Arg(name="module_name", type="str", description="Name of the module", required=False),
        Arg(name="module_source", type="str", description="Source of the module", required=False),
        Arg(name="module_path", type="str", description="Path to the Terraform module", required=False),
    ],
)

tool_registry.register("terraform", terraform_module_tool)