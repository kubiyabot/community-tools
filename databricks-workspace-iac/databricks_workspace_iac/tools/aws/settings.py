# AWS-specific settings
AWS_BACKEND_BUCKET = 'my-test-backend-bucket'
AWS_BACKEND_REGION = 'us-west-2'
AWS_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/aws'

# Define a function to create Terraform variable strings
def tf_var(name, description, required=False, default=None):
    return {
        "name": name,
        "description": description,
        "required": required,
        "default": default
    }

# Terraform variables
TF_VARS = [
    tf_var("workspace_name", "The name of the Databricks workspace to be created", required=True),
    tf_var("databricks_account_id", "The Databricks account ID", required=True, default="${DB_ACCOUNT_ID}"),
    tf_var("databricks_client_id", "The Databricks client ID", required=True, default="${DB_ACCOUNT_CLIENT_ID}"),
    tf_var("databricks_client_secret", "The Databricks client secret", required=True, default="${DB_ACCOUNT_CLIENT_SECRET}"),
]

# Git clone command
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'

# Mermaid diagram
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

# Required environment variables
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH", "DIR",
    "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION", "AWS_SECRET_ACCESS_KEY",
    "PAT"
]