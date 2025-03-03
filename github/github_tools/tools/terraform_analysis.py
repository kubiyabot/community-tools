from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

analyze_terraform_structure = GitHubCliTool(
    name="github_analyze_terraform_structure",
    description="Analyze repositories to find appropriate terraform module for new service",
    content="""
#!/bin/bash
set -e

# Analyze modules repository directly
echo "📁 Analyzing terraform modules repository..."
gh api "repos/${modules_repo}/git/trees/HEAD?recursive=1" | \
    jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > modules.txt

# Get modules content for better analysis
while read -r module_file; do
    echo "📄 Reading module: $module_file"
    gh api "repos/${modules_repo}/contents/$module_file" --jq '.content' | base64 -d >> modules_content.txt
    echo -e "\\n---\\n" >> modules_content.txt
done < modules.txt

# Analyze application repository directly
echo "📁 Analyzing application repository..."
gh api "repos/${app_repo}/git/trees/HEAD?recursive=1" | \
    jq -r '.tree[] | select(.path | endswith(".tf")) | .path' > app_files.txt

# Find appropriate module based on service requirements
echo "🔍 Finding appropriate module..."

# Check which terraform files exist in the specified path
echo "📁 Checking terraform files in ${app_path}..."
tf_files=$(grep "^${app_path}.*\.tf$" app_files.txt || true)

if [ -z "$tf_files" ]; then
    echo "❌ No terraform files found in ${app_path}"
    exit 1
fi

# Get content of existing terraform files
echo "📄 Reading terraform files..."
tf_content=""
while IFS= read -r file; do
    echo "Reading: $file"
    content=$(gh api "repos/${app_repo}/contents/$file" --jq '.content' | base64 -d 2>/dev/null)
    if [ -n "$content" ]; then
        tf_content+="$file:\\n$content\\n\\n"
    fi
done <<< "$tf_files"

module_selection=$(kubiya chat -n "terraform-self-service" --stream \
    --suggest-tool "github_create_branch_with_files" \
    --message "Find appropriate terraform module for new service and generate the terraform code to APPEND to existing files:
- Service name: ${service_name}
- Service type: ${service_type}
- Requirements: ${requirements}

Available modules in ${modules_repo}:
$(cat modules_content.txt)

EXISTING Terraform configuration in ${app_path}:
$tf_content

INSTRUCTIONS:
1. Find the most appropriate module from the available modules above
2. Generate the terraform code needed to add this new service
3. Format the response as updates to append to the existing files
4. DO NOT create new directories or files
5. DO NOT replace existing code, only append new code

Example response format:
\`\`\`hcl:${app_path}/main.tf
// ... existing code ...

# Add new service ${service_name}
module \"${service_name}\" {
  source = \"...\"
  // ... module configuration ...
}
\`\`\`

\`\`\`hcl:${app_path}/variables.tf
// ... existing code ...

# Variables for ${service_name}
variable \"${service_name}_config\" {
  // ... variable definition ...
}
\`\`\`")

echo "$module_selection"

# Cleanup
rm -f modules.txt modules_content.txt app_files.txt
""",
    args=[
        Arg(name="service_name", type="str", description="Name of the new service", required=True),
        Arg(name="service_type", type="str", description="Type of service being added", required=True),
        Arg(name="requirements", type="str", description="Service requirements and specifications", required=True),
        Arg(name="modules_repo", type="str", description="Repository containing terraform modules", required=True),
        Arg(name="app_repo", type="str", description="Application repository to analyze", required=True),
        Arg(name="app_path", type="str", description="Path to terraform files in application repo", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
    ]
)

tool_registry.register("github", analyze_terraform_structure)

__all__ = ['analyze_terraform_structure'] 