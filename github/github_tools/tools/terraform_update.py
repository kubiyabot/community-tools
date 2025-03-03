from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

update_terraform_config = GitHubCliTool(
    name="github_update_terraform_config",
    description="Update terraform configuration files and create branch",
    content="""
#!/bin/bash
set -e

# Get existing terraform files
echo "📄 Reading existing configuration..."
main_tf=$(kubiya run github_get_file \
    --repo "${app_repo}" \
    --file-path "${app_path}/main.tf" 2>/dev/null || echo "")
variables_tf=$(kubiya run github_get_file \
    --repo "${app_repo}" \
    --file-path "${app_path}/variables.tf" 2>/dev/null || echo "")
tfvars=$(kubiya run github_get_file \
    --repo "${app_repo}" \
    --file-path "${app_path}/terraform.tfvars" 2>/dev/null || echo "")

# Validate existing structure
if [ -z "$main_tf" ] || [ -z "$variables_tf" ]; then
    echo "❌ Could not find required terraform files."
    echo "Please specify correct path to terraform configuration."
    exit 1
fi

# Generate updated configuration
echo "🔧 Generating configuration updates..."
updated_config=$(kubiya chat -n "terraform" \
    --message "Update terraform configuration to add new service:
- Service name: ${service_name}
- Module source: ${module_source}
- Target path: ${app_path}
- IMPORTANT: Append only, preserve existing code

Current files:
main.tf:
${main_tf}

variables.tf:
${variables_tf}

terraform.tfvars:
${tfvars:-'# No existing tfvars'}")

# Create branch with updates and call PR creation tool
echo "🌱 Creating branch with updates..."
kubiya run github_create_branch_with_files \
    --repo "${app_repo}" \
    --branch-name "terraform/${service_name}" \
    --base-branch "${base_branch:-main}" \
    --files "${updated_config}" \
    --commit-message "feat: add terraform configuration for ${service_name}"
""",
    args=[
        Arg(name="app_repo", type="str", description="Application repository to update", required=True),
        Arg(name="module_source", type="str", description="Source path of terraform module to use", required=True),
        Arg(name="service_name", type="str", description="Name of the new service", required=True),
        Arg(name="app_path", type="str", description="Path to terraform files in application repo", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from", required=False, default="main"),
    ]
)

tool_registry.register("github", update_terraform_config) 