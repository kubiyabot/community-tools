from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

create_branch_with_files = GitHubCliTool(
    name="github_create_branch_with_files",
    description="Create a new branch and add/modify terraform configurations based on reference modules",
    content="""
#!/bin/bash
set -e

# Ensure GitHub CLI is authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI is not authenticated"
    exit 1
fi

# Get GitHub token for git operations
GH_TOKEN=$(gh auth token)
REPO_URL="https://${GH_TOKEN}@github.com/${repo}.git"

echo "🌱 Creating new branch: $branch_name from ${base_branch:-main}"
echo "📂 Target Repository: $repo"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository..."
if ! gh repo clone "$repo" . -- -q; then
    echo "❌ Failed to clone repository"
    exit 1
fi

# Configure git identity
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Create and checkout new branch
echo "🌱 Creating branch..."
git checkout -b "$branch_name" "origin/${base_branch:-main}"

# Process terraform configuration files
if [ -n "${files:-}" ]; then
    echo "📝 Adding terraform configurations..."
    echo "$files" | jq -c '.[]' | while read -r file_info; do
        path=$(echo "$file_info" | jq -r '.path')
        content=$(echo "$file_info" | jq -r '.content')
        
        echo "📄 Creating/updating file: $path"
        mkdir -p "$(dirname "$path")"
        echo "$content" > "$path"
        git add "$path"
    done

    # Commit changes
    if git status --porcelain | grep '^[AM]'; then
        echo "💾 Committing changes..."
        git commit -m "${commit_message:-Add new service configuration}"
    fi
fi

# Push the branch
echo "🚀 Pushing to remote..."
if ! git push -u "$REPO_URL" "$branch_name"; then
    echo "❌ Failed to push branch"
    exit 1
fi

echo "✨ Branch '$branch_name' created successfully!"
echo "🔗 Branch URL: https://github.com/$repo/tree/$branch_name"

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Application repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Name of the new branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
        Arg(name="files", type="str", description="""JSON array of terraform files to create/update. Format:
[
    {
        "path": "terraform/services/new-service/main.tf",
        "content": "module 'new_service' { ... }"
    },
    {
        "path": "terraform/services/new-service/variables.tf",
        "content": "variable 'service_name' { ... }"
    }
]""", required=False),
        Arg(name="commit_message", type="str", description="Commit message for terraform changes", required=False),
    ]
)

# Register tool
tool_registry.register("github", create_branch_with_files)

__all__ = ['create_branch_with_files'] 