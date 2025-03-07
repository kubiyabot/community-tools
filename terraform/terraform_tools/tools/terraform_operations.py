from kubiya_sdk.tools import Arg
from terraform_tools.tools.base import TerraformTool
from kubiya_sdk.tools.registry import tool_registry

terraform_clone_module = TerraformTool(
    name="terraform_clone_module",
    description="Clone a Terraform module from a Git repository and prepare it for use.",
    content="""
    #!/bin/bash
    set -e
    
    if [ -z "$git_repo" ]; then
        echo "Error: Git repository URL is required."
        exit 1
    fi

    git clone "$git_repo" module
    cd module

    if [ -n "$git_branch" ]; then
        git checkout "$git_branch"
    fi

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    echo "Module cloned successfully. Directory structure:"
    find . -maxdepth 2 -type d

    echo "Terraform files in the module:"
    find . -maxdepth 1 -name "*.tf" -printf "%f\n"
    """,
    args=[
        Arg(name="git_repo", type="str", description="Git repository URL containing the Terraform module. Example: 'https://github.com/example/terraform-aws-vpc.git'", required=True),
        Arg(name="git_branch", type="str", description="Git branch to use. Default is the repository's default branch. Example: 'develop'", required=False),
        Arg(name="module_path", type="str", description="Path to the module within the repository, if not in the root. Example: 'modules/networking'", required=False),
    ]
)

terraform_discover_variables = TerraformTool(
    name="terraform_discover_variables",
    description="Discover and list variables needed for a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    # Function to extract variables from Terraform files
    extract_variables() {
        grep -h '^\s*variable' *.tf | sed 's/variable\s*"\([^"]*\)".*/\1/'
    }

    # Function to extract variables from tfvars files
    extract_tfvars() {
        for file in *.tfvars *.tfvars.json; do
            if [[ -f "$file" ]]; then
                case "$file" in
                    *.tfvars)
                        grep -v '^\s*#' "$file" | grep '=' | cut -d'=' -f1 | tr -d ' '
                        ;;
                    *.tfvars.json)
                        jq -r 'keys[]' "$file"
                        ;;
                esac
            fi
        done
    }

    # Main execution
    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    echo "Variables defined in Terraform files:"
    extract_variables

    echo "Variables defined in tfvars files:"
    extract_tfvars

    echo "Attempting to run terraform init to discover module variables..."
    if terraform init -backend=false > /dev/null 2>&1; then
        echo "Module variables (may include variables from nested modules):"
        terraform providers schema -json | jq -r '.provider_schemas."registry.terraform.io/hashicorp/aws".resource_schemas | keys[]'
    else
        echo "Failed to run terraform init. Unable to discover module variables."
    fi
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
    ]
)

terraform_plan_module = TerraformTool(
    name="terraform_plan_module",
    description="Generate and show an execution plan for a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    if [ -n "$tfvars_content" ]; then
        echo "$tfvars_content" > terraform.tfvars
    fi

    terraform init
    terraform plan -no-color
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format. Example: 'region = \"us-west-2\"\ninstance_type = \"t2.micro\"'", required=False),
    ]
)

terraform_apply_module = TerraformTool(
    name="terraform_apply_module",
    description="Apply changes defined in a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    if [ -n "$tfvars_content" ]; then
        echo "$tfvars_content" > terraform.tfvars
    fi

    terraform init
    terraform apply -auto-approve -no-color
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format. Example: 'region = \"us-west-2\"\ninstance_type = \"t2.micro\"'", required=False),
    ]
)

terraform_destroy_module = TerraformTool(
    name="terraform_destroy_module",
    description="Destroy resources managed by a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    if [ -n "$tfvars_content" ]; then
        echo "$tfvars_content" > terraform.tfvars
    fi

    terraform init
    terraform destroy -auto-approve -no-color
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
        Arg(name="tfvars_content", type="str", description="Terraform variables content as a string. Can be in HCL or JSON format. Example: 'region = \"us-west-2\"\ninstance_type = \"t2.micro\"'", required=False),
    ]
)

terraform_output_module = TerraformTool(
    name="terraform_output_module",
    description="Read and display output values from a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    terraform init
    terraform output -json
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
    ]
)

terraform_validate_module = TerraformTool(
    name="terraform_validate_module",
    description="Validate the configuration files in a Terraform module.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    terraform init
    terraform validate -json
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
    ]
)

terraform_read_readme = TerraformTool(
    name="terraform_read_readme",
    description="Read and display specific content from the module's README file.",
    content="""
    #!/bin/bash
    set -e

    if [ -n "$module_path" ]; then
        cd "$module_path"
    fi

    if [ ! -f "README.md" ]; then
        echo "README.md not found in the module directory."
        exit 1
    fi

    if [ -n "$search_term" ]; then
        echo "Searching for '$search_term' in README.md:"
        grep -i -C 3 "$search_term" README.md || echo "Search term not found."
    elif [ -n "$start_line" ] && [ -n "$end_line" ]; then
        echo "Displaying lines $start_line to $end_line of README.md:"
        sed -n "${start_line},${end_line}p" README.md
    else
        echo "First 10 lines of README.md:"
        head -n 10 README.md
        echo "..."
        echo "Use 'search_term' or 'start_line' and 'end_line' arguments for more specific content."
    fi
    """,
    args=[
        Arg(name="module_path", type="str", description="Path to the Terraform module. Example: '/path/to/module' or '.' for current directory", required=True),
        Arg(name="search_term", type="str", description="Term to search for in the README. Example: 'Usage'", required=False),
        Arg(name="start_line", type="int", description="Start line number to read from. Example: 15", required=False),
        Arg(name="end_line", type="int", description="End line number to read to. Example: 30", required=False),
    ]
)

# Add this new tool to the existing file

terraform_append_block = TerraformTool(
    name="terraform_append_block",
    description="Append a Terraform block to an existing file and validate the resulting configuration.",
    content="""
    #!/bin/bash
    set -e

    if [ -z "$file_path" ] || [ -z "$block_content" ]; then
        echo "Error: Both file_path and block_content are required."
        exit 1
    fi

    if [ ! -f "$file_path" ]; then
        echo "Error: File $file_path does not exist."
        exit 1
    fi

    # Append the new block to the file
    echo -e "\n$block_content" >> "$file_path"

    echo "Block appended to $file_path"

    # Validate the updated configuration
    echo "Validating the updated configuration..."
    if terraform fmt -check "$file_path" > /dev/null 2>&1; then
        echo "Formatting check passed."
    else
        echo "Warning: Formatting issues detected. Running terraform fmt..."
        terraform fmt "$file_path"
    fi

    if terraform validate $(dirname "$file_path") > /dev/null 2>&1; then
        echo "Validation successful. The appended block is valid Terraform code."
    else
        echo "Error: Validation failed. The appended block may contain errors."
        echo "Validation output:"
        terraform validate $(dirname "$file_path")
        exit 1
    fi

    # Display the updated file content
    echo "Updated file content:"
    cat "$file_path"
    """,
    args=[
        Arg(name="file_path", type="str", description="Path to the Terraform file to append to. Example: '/path/to/main.tf'", required=True),
        Arg(name="block_content", type="str", description="Terraform block content to append. Example: 'resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-tf-test-bucket\"\n  acl    = \"private\"\n}'", required=True),
    ]
)

# Register the tools
tool_registry.register("terraform", terraform_clone_module)
tool_registry.register("terraform", terraform_read_readme)
tool_registry.register("terraform", terraform_discover_variables)
tool_registry.register("terraform", terraform_plan_module)
tool_registry.register("terraform", terraform_apply_module)
tool_registry.register("terraform", terraform_destroy_module)
tool_registry.register("terraform", terraform_output_module)
tool_registry.register("terraform", terraform_validate_module)
tool_registry.register("terraform", terraform_append_block)

__all__ = [
    'terraform_clone_module',
    'terraform_read_readme',
    'terraform_discover_variables',
    'terraform_plan_module',
    'terraform_apply_module',
    'terraform_destroy_module',
    'terraform_output_module',
    'terraform_validate_module',
    'terraform_append_block'
]