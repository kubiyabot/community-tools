from kubiya_sdk.tools import Arg
from .base import BasicGitHubTool
from kubiya_sdk.tools.registry import tool_registry

analyze_terraform_structure = BasicGitHubTool(
    name="github_analyze_terraform_structure",
    description="Gather terraform files information and determine required changes",
    content="""
#!/bin/bash
set -e

echo "🚀 Starting terraform analysis with:"
echo "- Service name: ${service_name}"
echo "- Service type: ${service_type}"
echo "- Modules repo: ${modules_repo}"
echo "- App repo: ${app_repo}"
echo "- Base branch: ${base_branch}"
echo "----------------------------------------"

# Validate repository format
validate_repo() {
    local repo=$1
    echo "🔍 Validating repository format for: $repo"
    if [[ ! $repo =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
        echo "❌ Error: Invalid repository format for '$repo'"
        echo "Repository should be in format 'owner/repo'"
        exit 1
    fi
}

# Validate input repositories
validate_repo "${modules_repo}"
validate_repo "${app_repo}"

# Check repository access
check_repo_access() {
    local repo=$1
    echo "🔍 Verifying access to repository: $repo"
    echo "Running: gh repo view \"$repo\" --json name"
    if ! gh repo view "$repo" --json name >/dev/null 2>&1; then
        echo "❌ Error: Cannot access repository '$repo'"
        echo "Please check repository permissions and name"
        exit 1
    fi
}

check_repo_access "${modules_repo}"
check_repo_access "${app_repo}"

# Get default branch and tree
echo "📥 Fetching default branch for ${modules_repo}"
echo "Running: gh api \"repos/${modules_repo}\" --jq '.default_branch'"
default_branch=$(gh api "repos/${modules_repo}" --jq '.default_branch')
echo "Default branch: ${default_branch}"

echo "📂 Fetching repository tree for ${modules_repo}"
echo "Running: gh api \"repos/${modules_repo}/git/trees/${default_branch}?recursive=1\""
modules_tree=$(gh api "repos/${modules_repo}/git/trees/${default_branch}?recursive=1")

# Get all module files and their contents
echo "🔍 Finding Terraform files in modules repository"
echo "$modules_tree" | jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > modules.txt

echo "📄 Reading module contents:"
while read -r module_file; do
    echo "  - Reading: $module_file"
    echo "  Running: gh api \"repos/${modules_repo}/contents/$module_file\""
    module_content=$(gh api "repos/${modules_repo}/contents/$module_file" --jq '.content' 2>/dev/null || echo "")
    if [ -n "$module_content" ]; then
        echo "$module_content" | base64 -d >> modules_content.txt
        echo -e "\\n---\\n" >> modules_content.txt
    fi
done < modules.txt

# Analyze application repository
echo "📂 Fetching repository tree for ${app_repo}"
echo "Running: gh api \"repos/${app_repo}/git/trees/${base_branch}?recursive=1\""
app_tree=$(gh api "repos/${app_repo}/git/trees/${base_branch}?recursive=1") || {
    echo "❌ Failed to fetch repository tree"
    exit 1
}

# Find terraform files
echo "🔍 Finding Terraform files"
echo "$app_tree" | jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > app_files.txt || {
    echo "❌ Failed to process repository tree"
    exit 1
}

# Check if any terraform files were found
if [ ! -s app_files.txt ]; then
    echo "❌ No Terraform files found in repository"
    exit 1
fi

# Find terraform directories
echo "🔍 Finding Terraform directories"
echo "Processing terraform files to find directories..."

# Process directories one at a time
touch tf_directories.txt
while IFS= read -r file; do
    dir=$(dirname "$file") || {
        echo "❌ Failed to process directory for file: $file"
        exit 1
    }
    echo "$dir" >> tf_directories.txt
done < app_files.txt

# Sort and deduplicate the directories
sort -u tf_directories.txt > tf_directories.tmp && mv tf_directories.tmp tf_directories.txt

# Check if directories file was created successfully
if [ ! -s tf_directories.txt ]; then
    echo "❌ Failed to identify Terraform directories"
    exit 1
fi

tf_dirs=$(cat tf_directories.txt)

# For each directory, gather its terraform content
for dir in $tf_dirs; do
    echo "📁 Processing directory: $dir"
    tf_files=$(grep "^${dir}.*\.tf$" app_files.txt || true)
    
    if [ -n "$tf_files" ]; then
        while IFS= read -r file; do
            echo "  - Reading: $file"
            echo "  Running: gh api \"repos/${app_repo}/contents/$file\""
            content=$(gh api "repos/${app_repo}/contents/$file" --jq '.content' | base64 -d 2>/dev/null)
            if [ -n "$content" ]; then
                echo "FILE:$file" >> app_content.txt
                echo "$content" >> app_content.txt
                echo "---" >> app_content.txt
            fi
        done <<< "$tf_files"
    fi
done

echo "🤖 Analyzing terraform structure and suggesting changes..."
# Analyze and determine changes
kubiya chat -n "terraform-self-service" --stream \
    --suggest-tool "github_terraform_updater" \
    --message "Find appropriate terraform module for new service and determine required changes:
- Service name: ${service_name}
- Service type: ${service_type}
- Requirements: ${requirements}

Available modules:
$(cat modules_content.txt)

Existing Terraform configuration:
$(cat app_content.txt)

INSTRUCTIONS:
1. Find the most appropriate module from the available modules
2. Determine which existing terraform files need updates
3. Generate the required terraform code
4. Specify if new files need to be created"

echo "🧹 Cleaning up temporary files..."
# Cleanup
rm -f modules.txt modules_content.txt app_files.txt app_content.txt tf_directories.txt

echo "✅ Analysis complete!"
""",
    args=[
        Arg(name="service_name", type="str", description="Name of the new service", required=True),
        Arg(name="service_type", type="str", description="Type of service being added", required=True),
        Arg(name="requirements", type="str", description="Service requirements and specifications", required=True),
        Arg(name="modules_repo", type="str", description="Repository containing terraform modules", required=True),
        Arg(name="app_repo", type="str", description="Application repository to analyze", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
    ]
)

tool_registry.register("github", analyze_terraform_structure)

__all__ = ['analyze_terraform_structure'] 