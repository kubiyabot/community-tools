from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

create_terraform_pr = GitHubCliTool(
    name="github_create_terraform_pr",
    description="Create pull request for terraform changes",
    content="""
#!/bin/bash
set -e

# Create PR
echo "📝 Creating pull request..."
kubiya run github_create_pr \
    --repo "${repo}" \
    --title "feat: add terraform configuration for ${service_name}" \
    --body "Adds terraform configuration for new ${service_name} service" \
    --base "${base_branch:-main}" \
    --head "terraform/${service_name}"

echo "✨ Pull request created successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="service_name", type="str", description="Name of the new service", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create PR against", required=False, default="main"),
    ]
)

tool_registry.register("github", create_terraform_pr) 