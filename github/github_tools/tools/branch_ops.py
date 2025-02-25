from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

create_branch_with_files = GitHubCliTool(
    name="github_create_branch_with_files",
    description="Create a new branch and add terraform module files from a template repository",
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
TEMPLATE_REPO_URL="https://${GH_TOKEN}@github.com/${template_repo}.git"

echo "🔍 Fetching module from template repository: ${template_repo}"
echo "🌱 Creating new branch: $branch_name from ${base_branch:-main}"
echo "📂 Target Repository: $repo"

# Create temporary directories
TEMP_DIR=$(mktemp -d)
TEMPLATE_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone both repositories
echo "📥 Cloning repositories..."
if ! gh repo clone "$repo" . -- -q; then
    echo "❌ Failed to clone target repository"
    exit 1
fi

if ! gh repo clone "$template_repo" "$TEMPLATE_DIR" -- -q; then
    echo "❌ Failed to clone template repository"
    exit 1
fi

# Configure git identity
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Create and checkout new branch
echo "🌱 Creating branch..."
git checkout -b "$branch_name" "origin/${base_branch:-main}"

# Process module files if provided
if [ -n "${module_path:-}" ]; then
    echo "📝 Copying module files..."
    mkdir -p "$(dirname "$module_path")"
    cp -r "$TEMPLATE_DIR/modules/$module_path" ./"$target_path"
    git add "$target_path"
fi

# Process additional files if provided
if [ -n "${files:-}" ]; then
    echo "📝 Processing additional files..."
    echo "$files" | jq -c '.[]' | while read -r file_info; do
        path=$(echo "$file_info" | jq -r '.path')
        content=$(echo "$file_info" | jq -r '.content')
        
        echo "📄 Creating file: $path"
        mkdir -p "$(dirname "$path")"
        echo "$content" > "$path"
        git add "$path"
    done
fi

# Commit changes if files were added
if git status --porcelain | grep '^[AM]'; then
    echo "💾 Committing changes..."
    git commit -m "${commit_message:-Add new service module via Kubiya}"
fi

# Push the branch with changes
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
rm -rf "$TEMPLATE_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Target repository name (owner/repo)", required=True),
        Arg(name="template_repo", type="str", description="Template repository containing modules (owner/repo)", required=False, default="kubiya-solutions-engineering/tf-modules"),
        Arg(name="module_path", type="str", description="Path to the module in template repository (e.g., 'alb' or 'ecs')", required=False),
        Arg(name="target_path", type="str", description="Target path in destination repository", required=False),
        Arg(name="branch_name", type="str", description="Name of the new branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
        Arg(name="files", type="str", description="""JSON array of additional files to create. Format:
[
    {
        "path": "path/to/file1.tf",
        "content": "module content here"
    }
]""", required=False),
        Arg(name="commit_message", type="str", description="Commit message for file changes", required=False),
    ]
)

# Register tool
tool_registry.register("github", create_branch_with_files)

__all__ = ['create_branch_with_files'] 