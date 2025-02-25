from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

create_branch = GitHubCliTool(
    name="github_create_branch",
    description="Create a new branch in a GitHub repository",
    content="""
#!/bin/bash
set -e

echo "🌱 Creating new branch: $branch_name"
echo "📂 Repository: $repo"
echo "🔄 Base branch: ${base_branch:-main}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository..."
if ! gh repo clone "$repo" .; then
    echo "❌ Failed to clone repository"
    exit 1
fi

# Configure git
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Fetch and checkout base branch
echo "🔄 Fetching latest changes..."
git fetch origin "${base_branch:-main}"
git checkout "${base_branch:-main}"
git pull origin "${base_branch:-main}"

# Create and push new branch
echo "🌱 Creating branch: $branch_name"
if ! git checkout -b "$branch_name"; then
    echo "❌ Failed to create branch"
    exit 1
fi

# Push the new branch
echo "🚀 Pushing branch to remote..."
if ! git push -u origin "$branch_name"; then
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
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Name of the new branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
    ]
)

create_files = GitHubCliTool(
    name="github_create_files",
    description="Create one or more files in a GitHub repository branch",
    content="""
#!/bin/bash
set -e

echo "📝 Creating files in repository: $repo"
echo "🌱 Branch: $branch_name"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository..."
if ! gh repo clone "$repo" .; then
    echo "❌ Failed to clone repository"
    exit 1
fi

# Configure git
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Checkout target branch
echo "🔄 Checking out branch: $branch_name"
if ! git fetch origin "$branch_name" && ! git checkout "$branch_name"; then
    echo "❌ Branch not found or checkout failed"
    exit 1
fi

# Process files
echo "📝 Processing files..."
echo "$files" | jq -c '.[]' | while read -r file_info; do
    path=$(echo "$file_info" | jq -r '.path')
    content=$(echo "$file_info" | jq -r '.content')
    
    echo "📄 Creating file: $path"
    
    # Create directory structure if needed
    mkdir -p "$(dirname "$path")"
    
    # Write file content
    echo "$content" > "$path"
    
    # Add file to git
    git add "$path"
done

# Commit changes
if git status --porcelain | grep '^[AM]'; then
    echo "💾 Committing changes..."
    git commit -m "${commit_message:-Add new files via Kubiya}"
    
    echo "🚀 Pushing changes..."
    if ! git push origin "$branch_name"; then
        echo "❌ Failed to push changes"
        exit 1
    fi
    
    echo "✨ Files created successfully!"
    echo "🔗 Branch URL: https://github.com/$repo/tree/$branch_name"
else
    echo "ℹ️ No changes to commit"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Branch name to create files in", required=True),
        Arg(name="files", type="str", description="""JSON array of files to create. Format:
[
    {
        "path": "path/to/file1.txt",
        "content": "file content here"
    },
    {
        "path": "path/to/file2.md",
        "content": "# Title\\nContent here"
    }
]""", required=True),
        Arg(name="commit_message", type="str", description="Commit message", required=False),
    ]
)

# Register tools
for tool in [create_branch, create_files]:
    tool_registry.register("github", tool)

__all__ = ['create_branch', 'create_files'] 