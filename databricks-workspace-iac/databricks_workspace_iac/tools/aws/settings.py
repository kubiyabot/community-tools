from ..shared_templates import tf_var, GIT_CLONE_COMMAND, COMMON_WORKSPACE_TEMPLATE, WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING, ERROR_NOTIFICATION_TEMPLATE

# AWS-specific settings for Databricks workspace creation

# S3 bucket for Terraform state storage
AWS_BACKEND_BUCKET = 'my-test-backend-bucket'

# AWS region for the Terraform backend
AWS_BACKEND_REGION = 'us-west-2'

# Directory containing Terraform files for AWS
AWS_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/aws'

# Terraform variables
TF_VARS = [
    tf_var("workspace_name", "The name of the Databricks workspace to be created", required=True),
    tf_var("databricks_account_id", "The Databricks account ID", required=True, default="${DB_ACCOUNT_ID}"),
    tf_var("databricks_client_id", "The Databricks client ID for authentication", required=True, default="${DB_ACCOUNT_CLIENT_ID}"),
    tf_var("databricks_client_secret", "The Databricks client secret for authentication", required=True, default="${DB_ACCOUNT_CLIENT_SECRET}"),
    tf_var("aws_region", "The AWS region where the workspace will be created", required=False, default="us-west-2"),
    tf_var("vpc_cidr", "The CIDR block for the VPC", required=False, default="10.4.0.0/16"),
    tf_var("subnet_public_cidr", "The CIDR block for the public subnet", required=False, default="10.4.1.0/24"),
    tf_var("subnet_private_cidr", "The CIDR block for the private subnet", required=False, default="10.4.2.0/24"),
]

# Mermaid diagram for visualizing the workflow
MERMAID_DIAGRAM = """
flowchart TD
    %% User interaction
    User -->|🗨 Request AWS Databricks Workspace| Teammate
    Teammate -->|🗨 What workspace name do you want?| User
    User -->|🏷 Workspace Name: my-workspace| Teammate
    Teammate -->|🚀 Starting AWS Terraform Apply| ApplyAWS

    %% AWS Execution
    subgraph AWS Environment
        ApplyAWS[AWS Kubernetes Job]
        ApplyAWS -->|Running Terraform on AWS 🛠| K8sAWS[Checking Status 🔄]
        K8sAWS -->|⌛ Waiting for Completion| DatabricksAWS[Databricks Workspace Created 🎉]
        ApplyAWS -->|Uses| TerraformDockerAWS[Terraform Docker 🐳]
    end

    %% Feedback to User
    K8sAWS -->|✅ Success! Workspace Ready| Teammate
    Teammate -->|🎉 Workspace is ready!| User
"""

# Required environment variables for the tool to function
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH", "DIR", "AWS_PROFILE",
    "PAT", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "SLACK_API_TOKEN"
]

# AWS-specific template parameters
AWS_TEMPLATE_PARAMS = {
    "TERRAFORM_DIR": AWS_TERRAFORM_DIR,
    "CHECK_REQUIRED_VARS": ' '.join([f'check_var "${{{var}}}"' for var in REQUIRED_ENV_VARS]),
    "TERRAFORM_INIT_COMMAND": f'terraform init -backend-config="bucket={AWS_BACKEND_BUCKET}" \\\n    -backend-config="key=databricks/${{workspace_name}}/terraform.tfstate" \\\n    -backend-config="region={AWS_BACKEND_REGION}"',
    "TERRAFORM_VARS": ' '.join([f'-var "{var["name"]}=${{{var["name"]}}}"' for var in TF_VARS]),
    "FALLBACK_WORKSPACE_URL": "https://accounts.cloud.databricks.com/workspaces?account_id=${DB_ACCOUNT_ID}",
    "BACKEND_TYPE": "s3",
    "IMPORT_COMMAND": "terraform import aws_databricks_workspace.this ${workspace_name}"
}

# Complete workspace creation template for AWS
AWS_WORKSPACE_TEMPLATE = COMMON_WORKSPACE_TEMPLATE.format(**AWS_TEMPLATE_PARAMS)

# Wrap the workspace template with error handling
AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING.format(
    WORKSPACE_TEMPLATE=AWS_WORKSPACE_TEMPLATE,
    ERROR_NOTIFICATION_TEMPLATE=ERROR_NOTIFICATION_TEMPLATE
)

# Export variables for use in other modules
__all__ = ['AWS_TERRAFORM_DIR', 'TF_VARS', 'GIT_CLONE_COMMAND', 'MERMAID_DIAGRAM', 'REQUIRED_ENV_VARS', 'AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING']