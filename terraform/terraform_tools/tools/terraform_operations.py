from kubiya_sdk.tools import Arg
from .base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_init = TerraformTool(
    name="terraform_init",
    description="Initialize a Terraform working directory",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    echo "Terraform initialization successful"
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_plan = TerraformTool(
    name="terraform_plan",
    description="Generate and show an execution plan",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform plan -no-color 2>&1 || { echo "Error: Terraform plan failed"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_apply = TerraformTool(
    name="terraform_apply",
    description="Builds or changes infrastructure",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform apply -auto-approve -no-color 2>&1 || { echo "Error: Terraform apply failed"; exit 1; }
    echo "Terraform apply completed successfully"
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_destroy = TerraformTool(
    name="terraform_destroy",
    description="Destroy Terraform-managed infrastructure",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform destroy -auto-approve -no-color 2>&1 || { echo "Error: Terraform destroy failed"; exit 1; }
    echo "Terraform destroy completed successfully"
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_output = TerraformTool(
    name="terraform_output",
    description="Read an output from a Terraform state",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform output -json 2>&1 || { echo "Error: Terraform output failed"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
        Arg(name="output_name", type="str", description="Name of the specific output to retrieve. If not provided, all outputs will be shown.", required=False),
    ]
)

terraform_show = TerraformTool(
    name="terraform_show",
    description="Inspect Terraform state or plan",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform show -json 2>&1 || { echo "Error: Terraform show failed"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_validate = TerraformTool(
    name="terraform_validate",
    description="Validates the Terraform files",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform validate -json 2>&1 || { echo "Error: Terraform validate failed"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_workspace_list = TerraformTool(
    name="terraform_workspace_list",
    description="List Terraform workspaces",
    content="""
    terraform workspace list 2>&1 || { echo "Error: Failed to list Terraform workspaces"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_workspace_select = TerraformTool(
    name="terraform_workspace_select",
    description="Select a Terraform workspace",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform workspace select "$workspace_name" 2>&1 || terraform workspace new "$workspace_name" 2>&1 || { echo "Error: Failed to select or create workspace"; exit 1; }
    echo "Workspace '$workspace_name' selected or created successfully"
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
        Arg(name="workspace_name", type="str", description="Name of the workspace to select or create.", required=True),
    ]
)

terraform_state_list = TerraformTool(
    name="terraform_state_list",
    description="List resources in the Terraform state",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform state list 2>&1 || { echo "Error: Failed to list Terraform state"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
)

terraform_state_show = TerraformTool(
    name="terraform_state_show",
    description="Show a resource in the Terraform state",
    content="""
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform state show "$resource_address" 2>&1 || { echo "Error: Failed to show resource in Terraform state"; exit 1; }
    """,
    args=[
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
        Arg(name="resource_address", type="str", description="Address of the resource to show.", required=True),
    ]
)

# Register the tools
tool_registry.register("terraform", terraform_init)
tool_registry.register("terraform", terraform_plan)
tool_registry.register("terraform", terraform_apply)
tool_registry.register("terraform", terraform_destroy)
tool_registry.register("terraform", terraform_output)
tool_registry.register("terraform", terraform_show)
tool_registry.register("terraform", terraform_validate)
tool_registry.register("terraform", terraform_workspace_list)
tool_registry.register("terraform", terraform_workspace_select)
tool_registry.register("terraform", terraform_state_list)
tool_registry.register("terraform", terraform_state_show)

__all__ = [
    'terraform_init',
    'terraform_plan',
    'terraform_apply',
    'terraform_destroy',
    'terraform_output',
    'terraform_show',
    'terraform_validate',
    'terraform_workspace_list',
    'terraform_workspace_select',
    'terraform_state_list',
    'terraform_state_show'
]