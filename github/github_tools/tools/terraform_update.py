from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

github_terraform_updater = GitHubCliTool(
    name="github_terraform_updater",
    description="Create or update terraform files based on analysis",
    content="""
#!/bin/bash
set -e

# Create new branch for changes
echo "🌿 Creating new branch..."
branch_name="terraform-update-${service_name}-$(date +%s)"
gh api -X POST "repos/${app_repo}/git/refs" \
    -f ref="refs/heads/${branch_name}" \
    -f sha="$(gh api "repos/${app_repo}/git/refs/heads/${base_branch}" --jq '.object.sha')"

# Process each file from the changes
echo "${changes}" | while IFS= read -r line; do
    if [[ $line == \`\`\`* ]]; then
        # Extract file path from the markdown code block header
        file_path=$(echo "$line" | sed -n 's/^```[^:]*:\([^[:space:]]*\).*/\1/p')
        if [ -n "$file_path" ]; then
            echo "📝 Processing changes for: $file_path"
            # Read until the closing code block
            content=""
            while IFS= read -r content_line; do
                if [[ $content_line == \`\`\`* ]]; then
                    break
                fi
                content="${content}${content_line}\\n"
            done
            
            # Create or update file in the repository
            echo "💾 Updating $file_path..."
            echo -e "$content" | gh api -X PUT "repos/${app_repo}/contents/${file_path}" \
                -f message="feat(terraform): Add ${service_name} service configuration" \
                -f content="$(echo -e "$content" | base64)" \
                -f branch="$branch_name" \
                --input - || {
                echo "⚠️ Failed to update $file_path, trying to create it..."
                echo -e "$content" | gh api -X PUT "repos/${app_repo}/contents/${file_path}" \
                    -f message="feat(terraform): Add ${service_name} service configuration" \
                    -f content="$(echo -e "$content" | base64)" \
                    -f branch="$branch_name" \
                    --input -
            }
        fi
    fi
done

# Create pull request
echo "🔄 Creating pull request..."
gh pr create \
    --repo "${app_repo}" \
    --base "${base_branch}" \
    --head "${branch_name}" \
    --title "feat(terraform): Add ${service_name} service" \
    --body "Add terraform configuration for ${service_name} service

Changes:
- Add terraform module for ${service_name}
- Configure service based on requirements
- Update necessary variables and outputs

Service Type: ${service_type}
Requirements: ${requirements}"
""",
    args=[
        Arg(name="changes", type="str", description="Terraform changes to implement", required=True),
        Arg(name="app_repo", type="str", description="Repository to update", required=True),
        Arg(name="service_name", type="str", description="Name of the new service", required=True),
        Arg(name="service_type", type="str", description="Type of service being added", required=True),
        Arg(name="requirements", type="str", description="Service requirements and specifications", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
    ]
)

tool_registry.register("github", github_terraform_updater)

__all__ = ['github_terraform_updater']