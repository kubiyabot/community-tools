from kubiya_sdk.tools import Arg
from terraform.terraform_tools.tools.base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

def create_terraform_tool(name, description, content, additional_args=None):
    args = [
        Arg(name="terraform_code", type="str", description="Terraform configuration code as a string. Example: 'resource \"aws_s3_bucket\" \"example\" { bucket = \"my-tf-test-bucket\" }'", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format. Example: 'region = \"us-west-2\"\ninstance_type = \"t2.micro\"'", required=False),
        Arg(name="git_repo", type="str", description="Git repository URL containing Terraform code. Example: 'https://github.com/example/terraform-module.git'", required=False),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is 'main'", required=False),
    ]
    if additional_args:
        args.extend(additional_args)

    return TerraformTool(
        name=f"terraform_{name}",
        description=description,
        content=f"""
        #!/bin/bash
        set -e

        TEMP_DIR=$(mktemp -d)
        trap 'rm -rf "$TEMP_DIR"' EXIT
        cd "$TEMP_DIR"

        if [ -n "$git_repo" ]; then
            git clone "$git_repo" .
            if [ -n "$git_branch" ]; then
                git checkout "$git_branch"
            fi
        else
            echo "$terraform_code" > main.tf
            [ -n "$tfvars_content" ] && echo "$tfvars_content" > terraform.tfvars
        fi

        {content}

        cd - > /dev/null
        """,
        args=args
    )

terraform_init = create_terraform_tool(
    "init",
    "Initialize a Terraform working directory",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    echo "Terraform initialization successful"
    """
)

terraform_plan = create_terraform_tool(
    "plan",
    "Generate and show an execution plan",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform plan -no-color 2>&1 || { echo "Error: Terraform plan failed"; exit 1; }
    """
)

terraform_apply = create_terraform_tool(
    "apply",
    "Builds or changes infrastructure",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform apply -auto-approve -no-color 2>&1 || { echo "Error: Terraform apply failed"; exit 1; }
    echo "Terraform apply completed successfully"
    """
)

terraform_destroy = create_terraform_tool(
    "destroy",
    "Destroy Terraform-managed infrastructure",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform destroy -auto-approve -no-color 2>&1 || { echo "Error: Terraform destroy failed"; exit 1; }
    echo "Terraform destroy completed successfully"
    """
)

terraform_output = create_terraform_tool(
    "output",
    "Read an output from a Terraform state",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform output -json 2>&1 || { echo "Error: Terraform output failed"; exit 1; }
    """,
    additional_args=[
        Arg(name="output_name", type="str", description="Name of the specific output to retrieve. If not provided, all outputs will be shown. Example: 'vpc_id'", required=False),
    ]
)

terraform_show = create_terraform_tool(
    "show",
    "Inspect Terraform state or plan",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform show -json 2>&1 || { echo "Error: Terraform show failed"; exit 1; }
    """
)

terraform_validate = create_terraform_tool(
    "validate",
    "Validates the Terraform files",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform validate -json 2>&1 || { echo "Error: Terraform validate failed"; exit 1; }
    """
)

terraform_workspace_list = create_terraform_tool(
    "workspace_list",
    "List Terraform workspaces",
    """
    terraform workspace list 2>&1 || { echo "Error: Failed to list Terraform workspaces"; exit 1; }
    """
)

terraform_workspace_select = create_terraform_tool(
    "workspace_select",
    "Select a Terraform workspace",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform workspace select "$workspace_name" 2>&1 || terraform workspace new "$workspace_name" 2>&1 || { echo "Error: Failed to select or create workspace"; exit 1; }
    echo "Workspace '$workspace_name' selected or created successfully"
    """,
    additional_args=[
        Arg(name="workspace_name", type="str", description="Name of the workspace to select or create. Example: 'development'", required=True),
    ]
)

terraform_state_list = create_terraform_tool(
    "state_list",
    "List resources in the Terraform state",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform state list 2>&1 || { echo "Error: Failed to list Terraform state"; exit 1; }
    """
)

terraform_state_show = create_terraform_tool(
    "state_show",
    "Show a resource in the Terraform state",
    """
    terraform init 2>&1 || { echo "Error: Terraform init failed"; exit 1; }
    terraform state show "$resource_address" 2>&1 || { echo "Error: Failed to show resource in Terraform state"; exit 1; }
    """,
    additional_args=[
        Arg(name="resource_address", type="str", description="Address of the resource to show. Example: 'aws_instance.example'", required=True),
    ]
)

# Register all tools
for tool in [
    terraform_init,
    terraform_plan,
    terraform_apply,
    terraform_destroy,
    terraform_output,
    terraform_show,
    terraform_validate,
    terraform_workspace_list,
    terraform_workspace_select,
    terraform_state_list,
    terraform_state_show,
]:
    tool_registry.register("terraform", tool)
