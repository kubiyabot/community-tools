from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry
import json

create_branch_with_files = GitHubCliTool(
    name="github_create_branch_with_files",
    description="""Create a new branch and add/modify files. 
    
    IMPORTANT: You must provide the complete file contents when calling this tool.
    The files parameter should be a list of dictionaries with the following structure:
    
    files = [
        {
            "path": "terraform/modules/services/alb/main.tf",
            "content": "resource 'aws_lb' 'main' {...}",
            "append": false
        }
    ]
    """,
    content="""
#!/bin/bash
set -e

# Convert files parameter to proper JSON if needed
if [[ "$files" == "["* ]]; then
    # Already looks like JSON, use as-is
    FILES_JSON="$files"
else
    # Try to evaluate as Python and convert to JSON
    FILES_JSON=$(python3 -c "import json, ast; print(json.dumps(ast.literal_eval('$files')))")
fi

# Validate files parameter
if [ -z "${FILES_JSON:-}" ]; then
    echo "❌ No files specified. Please provide at least one file to create/modify"
    echo "Files should be a JSON array with objects containing 'path' and 'content'"
    exit 1
fi

# Validate files JSON structure
echo "$FILES_JSON" | jq -e 'all(.[] | has("path") and has("content"))' >/dev/null || {
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
if [ -n "${FILES_JSON:-}" ]; then
    echo "📝 Processing files..."
    echo "$FILES_JSON" | jq -c '.[]' | while read -r file_info; do
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

# Create PR if requested
if [ "${create_pr}" = "true" ]; then
    echo "📝 Creating pull request..."
    PR_URL=$(gh pr create \
        --repo "$repo" \
        --base "${base_branch:-main}" \
        --head "$UNIQUE_BRANCH" \
        --title "${pr_title:-Add new service configuration}" \
        --body "${pr_body:-Add new service configuration}" \
        $([[ -n "${pr_reviewers}" ]] && echo "--reviewer ${pr_reviewers}") \
        $([[ -n "${pr_assignees}" ]] && echo "--assignee ${pr_assignees}"))
    
    if [ $? -eq 0 ]; then
        echo "✨ Pull request created successfully!"
        echo "🔗 PR URL: $PR_URL"
    else
        echo "❌ Failed to create pull request"
        echo "You can create it manually using the branch: $UNIQUE_BRANCH"
    fi
fi

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Base name for the branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
        Arg(name="files", type="list", description="""List of files to create/update. Each file must be a dictionary with:
            - path: File path in the repository (e.g., "terraform/modules/services/alb/main.tf")
            - content: Complete file content (e.g., the entire Terraform configuration)
            - append: (optional) Boolean to append instead of replace content""", 
            required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=False),
        Arg(name="create_pr", type="bool", description="Whether to create a PR after pushing the branch", required=False, default=False),
        Arg(name="pr_title", type="str", description="Title for the PR (if create_pr is true)", required=False),
        Arg(name="pr_body", type="str", description="Description for the PR (if create_pr is true)", required=False),
        Arg(name="pr_reviewers", type="str", description="Comma-separated list of PR reviewers (if create_pr is true)", required=False),
        Arg(name="pr_assignees", type="str", description="Comma-separated list of PR assignees (if create_pr is true)", required=False),
    ],
)

# Register tool
tool_registry.register("github", create_branch_with_files)

__all__ = ['create_branch_with_files'] 