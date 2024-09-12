from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_git_clone = TerraformTool(
    name="terraform_git_clone",
    description="Clone a Git repository containing Terraform configurations",
    content="""
    #!/bin/bash
    set -e
    git clone $repo_url $([[ -n "$branch" ]] && echo "-b $branch") $([[ -n "$directory" ]] && echo "$directory" || echo ".")
    """,
    args=[
        Arg(name="repo_url", type="str", description="URL of the Git repository", required=True),
        Arg(name="branch", type="str", description="Branch to clone (optional)", required=False),
        Arg(name="directory", type="str", description="Directory to clone into (optional)", required=False),
    ],
)

tool_registry.register("terraform", terraform_git_clone)