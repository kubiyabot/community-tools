from ..shared_templates import tf_var, GIT_CLONE_COMMAND, COMMON_WORKSPACE_TEMPLATE, WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING, ERROR_NOTIFICATION_TEMPLATE, generate_terraform_vars_json

# Add this line near the top of the file, after other similar definitions
TERRAFORM_MODULE_PATH = 'aux/databricks/terraform/aws'

# AWS-specific settings for Databricks workspace creation

# S3 bucket for Terraform state storage
AWS_BACKEND_BUCKET = 'my-test-backend-bucket'

# AWS region for the Terraform backend
AWS_BACKEND_REGION = 'us-west-2'

# Directory containing Terraform files for AWS
AWS_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/aws'

# Terraform variables
# For more information on these variables, see:
# https://registry.terraform.io/providers/databricks/databricks/latest/docs
TF_VARS = [
    tf_var("WORKSPACE_NAME", "The name of the Databricks workspace to be created", required=True),
    tf_var("aws_region", "The AWS region where the workspace will be created", required=True),
    tf_var("vpc_cidr", "The CIDR block for the VPC", required=False, default="10.4.0.0/16"),
    tf_var("subnet_public_cidr", "The CIDR block for the public subnet", required=False, default="10.4.1.0/24"),
    tf_var("subnet_private_cidr", "The CIDR block for the private subnet", required=False, default="10.4.2.0/24"),
    tf_var("databricks_account_id", "The Databricks account ID", required=True, default="${DB_ACCOUNT_ID}"),
    tf_var("databricks_account_console_url", "The Databricks account console URL", required=False, default="https://accounts.cloud.databricks.com"),
    tf_var("databricks_username", "The Databricks username", required=False),
    tf_var("databricks_password", "The Databricks password", required=False),
    tf_var("tags", "A map of tags to add to all resources", required=False),
    tf_var("root_bucket", "The root S3 bucket where data will be stored", required=False),
    tf_var("cross_account_arn", "The cross-account ARN for Databricks to access resources", required=False),
    tf_var("security_group_ids", "List of security group IDs to use for the workspace", required=False),
    tf_var("subnet_ids", "List of subnet IDs to use for the workspace", required=False),
    tf_var("vpc_id", "The ID of the VPC to use for the workspace", required=False),
    tf_var("managed_services_customer_managed_key_id", "The ID of the customer managed key for managed services", required=False),
    tf_var("storage_customer_managed_key_id", "The ID of the customer managed key for storage", required=False),
    tf_var("storage_configuration_name", "The name of the storage configuration", required=False),
    tf_var("enable_ip_access_list", "Enable IP access list for the workspace", required=False, default="false"),
    tf_var("ip_access_list", "List of IP addresses or CIDR blocks for the IP access list", required=False),
]

# Mermaid diagram for visualizing the workflow
MERMAID_DIAGRAM = """
flowchart TD
    %% User interaction
    User -->|🗨 Request AWS Databricks Workspace| Teammate
    Teammate -->|🗨 What workspace name and region?| User
    User -->|🏷 Workspace: my-workspace, Region: us-west-2| Teammate
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
    "CLOUD_PROVIDER": "AWS",
    "TERRAFORM_DIR": AWS_TERRAFORM_DIR,
    "CHECK_REQUIRED_VARS": ' '.join([f'check_var "${{{var}}}"' for var in REQUIRED_ENV_VARS]),
    "TERRAFORM_INIT_COMMAND": f'terraform init -backend-config="bucket={AWS_BACKEND_BUCKET}" \\\n    -backend-config="key=databricks/${{workspace_name}}/terraform.tfstate" \\\n    -backend-config="region={AWS_BACKEND_REGION}"',
    "TERRAFORM_VARS_JSON": generate_terraform_vars_json(TF_VARS),
    "FALLBACK_WORKSPACE_URL": "https://accounts.cloud.databricks.com/workspaces?account_id=${DB_ACCOUNT_ID}",
    "BACKEND_TYPE": "s3",
    "IMPORT_COMMAND": "terraform import aws_databricks_workspace.this ${workspace_name}",
    "GIT_CLONE_COMMAND": GIT_CLONE_COMMAND,
    "TERRAFORM_MODULE_PATH": TERRAFORM_MODULE_PATH
}

# Complete workspace creation template for AWS
AWS_WORKSPACE_TEMPLATE = COMMON_WORKSPACE_TEMPLATE.format(**AWS_TEMPLATE_PARAMS)

# Wrap the workspace template with error handling
AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING.format(
    WORKSPACE_TEMPLATE=AWS_WORKSPACE_TEMPLATE,
    ERROR_NOTIFICATION_TEMPLATE=ERROR_NOTIFICATION_TEMPLATE.format(CLOUD_PROVIDER="AWS")
)

# Export variables for use in other modules
__all__ = [
    'TERRAFORM_MODULE_PATH', 'TF_VARS', 'MERMAID_DIAGRAM', 
    'REQUIRED_ENV_VARS', 'AWS_WORKSPACE_TEMPLATE', 
    'AWS_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING'
]