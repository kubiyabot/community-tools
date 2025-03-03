from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

analyze_terraform_structure = GitHubCliTool(
    name="github_analyze_terraform_structure",
    description="Gather terraform files information and determine required changes",
    content="""
#!/bin/bash
set -e

# Debug: Print current user and their permissions
echo "🔍 Checking GitHub authentication..."
if ! gh auth status; then
    echo "❌ Error: Not authenticated with GitHub"
    exit 1
fi

# Debug: Print current user context
echo "👤 Current user context:"
gh api user --jq '.login'

# Analyze modules repository
echo "📁 Analyzing terraform modules repository '${modules_repo}'..."
if ! gh repo view "${modules_repo}" 2>/dev/null; then
    echo "❌ Error: Could not view repository '${modules_repo}'"
    echo "Please check repository access and name"
    exit 1
fi

# Get default branch and tree
default_branch=$(gh api "repos/${modules_repo}" --jq '.default_branch')
modules_tree=$(gh api "repos/${modules_repo}/git/trees/${default_branch}?recursive=1")

# Get all module files and their contents
echo "$modules_tree" | jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > modules.txt
while read -r module_file; do
    echo "📄 Reading module: $module_file"
    module_content=$(gh api "repos/${modules_repo}/contents/$module_file" --jq '.content' 2>/dev/null || echo "")
    if [ -n "$module_content" ]; then
        echo "$module_content" | base64 -d >> modules_content.txt
        echo -e "\\n---\\n" >> modules_content.txt
    fi
done < modules.txt

# Analyze application repository
echo "📁 Analyzing application repository..."
app_tree=$(gh api "repos/${app_repo}/git/trees/${base_branch}?recursive=1")
echo "$app_tree" | jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > app_files.txt

# Find terraform directories
tf_dirs=$(dirname $(cat app_files.txt) | sort -u)

# For each directory, gather its terraform content
for dir in $tf_dirs; do
    echo "📁 Processing directory: $dir"
    tf_files=$(grep "^${dir}.*\.tf$" app_files.txt || true)
    
    if [ -n "$tf_files" ]; then
        while IFS= read -r file; do
            content=$(gh api "repos/${app_repo}/contents/$file" --jq '.content' | base64 -d 2>/dev/null)
            if [ -n "$content" ]; then
                echo "FILE:$file" >> app_content.txt
                echo "$content" >> app_content.txt
                echo "---" >> app_content.txt
            fi
        done <<< "$tf_files"
    fi
done

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
4. Specify if new files need to be created

RESPONSE FORMAT:
Please format your response as a series of file changes, like this:

\`\`\`hcl:path/to/existing/file.tf
// ... existing code ...

module \"new_service\" {
    source = \"../modules/selected_module\"
    // ... configuration ...
}
\`\`\`

For new files:
\`\`\`hcl:path/to/new/file.tf
// Complete contents of new file
\`\`\`"

# Cleanup
rm -f modules.txt modules_content.txt app_files.txt app_content.txt
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