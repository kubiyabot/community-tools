from kubiya_sdk.tools import Arg
from .base import TerraformTool

def _create_terraform_tool(name, description, content, additional_args=None):
    args = [
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string.", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format.", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code.", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
    if additional_args:
        args.extend(additional_args)

    return TerraformTool(
        name=f"terraform_{name}",
        description=description,
        content=content,
        args=args,
        long_running=True
    )

# Define all the tools as before
def terraform_init():
    return _create_terraform_tool(
        "init",
        "Initialize a Terraform working directory",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        echo "Terraform initialization successful"
        """
    )

def terraform_plan():
    return _create_terraform_tool(
        "plan",
        "Generate and show an execution plan",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform plan -no-color 2>&1 || { echo "Error: Terraform plan failed"; exit 1; }
        """
    )

def terraform_apply():
    return _create_terraform_tool(
        "apply",
        "Builds or changes infrastructure",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform apply -auto-approve -no-color 2>&1 || { echo "Error: Terraform apply failed"; exit 1; }
        echo "Terraform apply completed successfully"
        """
    )

def terraform_destroy():
    return _create_terraform_tool(
        "destroy",
        "Destroy Terraform-managed infrastructure",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform destroy -auto-approve -no-color 2>&1 || { echo "Error: Terraform destroy failed"; exit 1; }
        echo "Terraform destroy completed successfully"
        """
    )

def terraform_output():
    return _create_terraform_tool(
        "output",
        "Read an output from a Terraform state",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform output -json 2>&1 || { echo "Error: Terraform output failed"; exit 1; }
        """,
        additional_args=[
            Arg(name="output_name", type="str", description="Name of the specific output to retrieve. If not provided, all outputs will be shown.", required=False),
        ]
    )

def terraform_show():
    return _create_terraform_tool(
        "show",
        "Inspect Terraform state or plan",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform show -json 2>&1 || { echo "Error: Terraform show failed"; exit 1; }
        """
    )

def terraform_validate():
    return _create_terraform_tool(
        "validate",
        "Validates the Terraform files",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform validate -json 2>&1 || { echo "Error: Terraform validate failed"; exit 1; }
        """
    )

def terraform_workspace_list():
    return _create_terraform_tool(
        "workspace_list",
        "List Terraform workspaces",
        """
        terraform workspace list 2>&1 || { echo "Error: Failed to list Terraform workspaces"; exit 1; }
        """
    )

def terraform_workspace_select():
    return _create_terraform_tool(
        "workspace_select",
        "Select a Terraform workspace",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform workspace select "$workspace_name" 2>&1 || terraform workspace new "$workspace_name" 2>&1 || { echo "Error: Failed to select or create workspace"; exit 1; }
        echo "Workspace '$workspace_name' selected or created successfully"
        """,
        additional_args=[
            Arg(name="workspace_name", type="str", description="Name of the workspace to select or create.", required=True),
        ]
    )

def terraform_state_list():
    return _create_terraform_tool(
        "state_list",
        "List resources in the Terraform state",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform state list 2>&1 || { echo "Error: Failed to list Terraform state"; exit 1; }
        """
    )

def terraform_state_show():
    return _create_terraform_tool(
        "state_show",
        "Show a resource in the Terraform state",
        """
        terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
        terraform state show "$resource_address" 2>&1 || { echo "Error: Failed to show resource in Terraform state"; exit 1; }
        """,
        additional_args=[
            Arg(name="resource_address", type="str", description="Address of the resource to show.", required=True),
        ]
    )

# Explicitly define __all__ to export the functions
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