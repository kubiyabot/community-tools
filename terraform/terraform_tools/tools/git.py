from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_git_tool = TerraformTool(
    name="terraform_git",
    description="Manages Git operations for Terraform",
    content="""
    case $action in
        clone)
            git clone $repo_url $([[ -n "$directory" ]] && echo "$directory")
            ;;
        pull)
            git pull
            ;;
        checkout)
            git checkout $branch
            ;;
        *)
            echo "Invalid action. Use 'clone', 'pull', or 'checkout'."
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Git action (clone, pull, checkout)", required=True),
        Arg(name="repo_url", type="str", description="URL of the Git repository", required=False),
        Arg(name="directory", type="str", description="Directory to clone into", required=False),
        Arg(name="branch", type="str", description="Branch to checkout", required=False),
    ],
)

tool_registry.register("terraform", terraform_git_tool)