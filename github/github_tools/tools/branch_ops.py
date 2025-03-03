from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

create_branch_with_files = GitHubCliTool(
    name="github_create_branch_with_files",
    description="""Create a new branch and add/modify files. 
    
    IMPORTANT: You must provide the complete file contents when calling this tool.
    Do not try to create files separately - include all file contents in the 'files' parameter.
    
    Example files parameter:
    [
        {
            "path": "terraform/modules/services/alb/main.tf",
            "content": "resource 'aws_lb' 'main' {...}",
            "append": false
        },
        {
            "path": "terraform/modules/services/alb/variables.tf",
            "content": "variable 'name' {...}",
            "append": false
        }
    ]
    """,
    content="""
#!/bin/bash
set -e

# Validate files parameter
if [ -z "${files:-}" ]; then
    echo "❌ No files specified. Please provide at least one file to create/modify"
    echo "Files should be a JSON array with objects containing 'path' and 'content'"
    exit 1
fi

# Validate files JSON structure
echo "$files" | jq -e 'all(.[] | has("path") and has("content"))' >/dev/null || {
    echo "❌ Invalid files format. Each file must have 'path' and 'content' fields"
    exit 1
}

# Ensure GitHub CLI is authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI is not authenticated"
    exit 1
fi

# Get GitHub token for git operations
GH_TOKEN=$(gh auth token)
REPO_URL="https://${GH_TOKEN}@github.com/${repo}.git"

# Generate unique branch name with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
UNIQUE_BRANCH="${branch_name}-${TIMESTAMP}"

echo "🌱 Creating new branch: $UNIQUE_BRANCH from ${base_branch:-main}"
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
git checkout -b "$UNIQUE_BRANCH" "origin/${base_branch:-main}"

# Process files
if [ -n "${files:-}" ]; then
    echo "📝 Processing files..."
    echo "$files" | jq -c '.[]' | while read -r file_info; do
        path=$(echo "$file_info" | jq -r '.path')
        content=$(echo "$file_info" | jq -r '.content')
        append_mode=$(echo "$file_info" | jq -r '.append // "false"')
        
        echo "📄 Processing file: $path"
        mkdir -p "$(dirname "$path")"
        
        if [ "$append_mode" = "true" ] && [ -f "$path" ]; then
            echo "📎 Appending to existing file..."
            echo -e "$(cat "$path")\\n${content}" > "$path"
        else
            echo "✏️  Creating/replacing file..."
            echo "$content" > "$path"
        fi
        
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
if ! git push "$REPO_URL" "$UNIQUE_BRANCH"; then
    echo "❌ Failed to push branch"
    exit 1
fi

echo "✨ Branch '$UNIQUE_BRANCH' created successfully!"
echo "🔗 Branch URL: https://github.com/$repo/tree/$UNIQUE_BRANCH"

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Base name for the branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
        Arg(name="files", type="str", description="""JSON array of files to create/update. You must include the complete file contents here.
            Each file must be an object with:
            - path: File path in the repository (e.g., "terraform/modules/services/alb/main.tf")
            - content: Complete file content (e.g., the entire Terraform configuration)
            - append: (optional) Boolean to append instead of replace content
            
            Do not try to create files separately - include all file contents in this parameter.""", 
            required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=False),
    ],
)

# Register tool
tool_registry.register("github", create_branch_with_files)

__all__ = ['create_branch_with_files'] 