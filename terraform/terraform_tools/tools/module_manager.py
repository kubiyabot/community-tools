from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_module_manager_tool = TerraformTool(
    name="terraform_module_manager",
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
        list-variables)
            if [ -n "$module_path" ]; then
                terraform-config-inspect --json $module_path | jq -r '.variables | keys[]'
            else
                echo "Module path is required for 'list-variables' action"
                exit 1
            fi
            ;;
        *)
            echo "Invalid action. Use 'get', 'use', or 'list-variables'."
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Module action (get, use, list-variables)", required=True),
        Arg(name="module_name", type="str", description="Name of the module", required=False),
        Arg(name="module_source", type="str", description="Source of the module", required=False),
        Arg(name="module_path", type="str", description="Path to the module for listing variables", required=False),
    ],
)

tool_registry.register("terraform", terraform_module_manager_tool)