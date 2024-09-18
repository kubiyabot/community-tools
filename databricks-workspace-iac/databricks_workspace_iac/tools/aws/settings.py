# AWS-specific settings for Databricks workspace creation

# S3 bucket for Terraform state storage
AWS_BACKEND_BUCKET = 'my-test-backend-bucket'

# AWS region for the Terraform backend
AWS_BACKEND_REGION = 'us-west-2'

# Directory containing Terraform files for AWS
AWS_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/aws'

# Function to create Terraform variable dictionaries
def tf_var(name, description, required=False, default=None):
    """
    Create a dictionary representing a Terraform variable.
    
    Args:
        name (str): Name of the variable
        description (str): Description of the variable
        required (bool): Whether the variable is required
        default (Any): Default value for the variable
    
    Returns:
        dict: A dictionary representing the Terraform variable
    """
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default
    }

# Terraform variables
# For more information on these variables, see:
# https://registry.terraform.io/providers/databricks/databricks/latest/docs
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

# Git clone command for fetching Terraform configurations
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'

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
    "PAT"
]

# Template for validating input parameters
VALIDATION_TEMPLATE = """
echo "🔍 Validating input parameters..."

# Function to check if a variable is set
check_var() {
    if [ -z "${!1}" ]; then
        echo "❌ Error: $1 is not set. Please provide it as an argument or environment variable."
        exit 1
    fi
}

# Check required variables
""" + "\n".join([f"check_var \"{var}\"" for var in REQUIRED_ENV_VARS]) + """

echo "✅ All required parameters are set."
"""

# Terraform initialization template
INIT_TEMPLATE = f"""
echo "🚀 Initializing Terraform..."
terraform init -backend-config="bucket={AWS_BACKEND_BUCKET}" \
  -backend-config="key=databricks/{{{{ .workspace_name}}}}/terraform.tfstate" \
  -backend-config="region={AWS_BACKEND_REGION}"
"""

# Terraform apply template
APPLY_TEMPLATE = """
echo "🏗️ Applying Terraform configuration..."
terraform apply -auto-approve """ + " ".join([f"-var \"{var['name']}={{{{ .{var['name']} }}}}\"" for var in TF_VARS])

# Output template for displaying results
OUTPUT_TEMPLATE = f"""
echo "📊 Capturing Terraform output..."
tf_output=$(terraform output -json || echo "{{}}")
workspace_url=$(echo "$tf_output" | jq -r '.databricks_host.value // empty')
workspace_url=${{workspace_url:-"https://accounts.cloud.databricks.com/workspaces?account_id=${{DB_ACCOUNT_ID}}"}}

echo "🔍 Getting backend config..."
backend_config=$(terraform show -json | jq -r '.values.backend_config // empty')

echo "The state file can be found here: https://{AWS_BACKEND_BUCKET}.s3.{AWS_BACKEND_REGION}.amazonaws.com/aws/"
echo "The databricks workspace can be found here: $workspace_url"
"""

# Complete workspace creation template
AWS_WORKSPACE_TEMPLATE = f"""
echo "🛠️ Setting up Databricks workspace on AWS..."
{GIT_CLONE_COMMAND}
cd {AWS_TERRAFORM_DIR}

{VALIDATION_TEMPLATE}
{INIT_TEMPLATE}
{APPLY_TEMPLATE}
{OUTPUT_TEMPLATE}

echo "✅ Databricks workspace setup complete!"
"""