# AWS-specific settings
AWS_BACKEND_BUCKET = 'my-test-backend-bucket'
AWS_BACKEND_REGION = 'us-west-2'
AWS_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/aws'

# Define a function to create Terraform variable strings
def tf_var(name, value=None):
    if value is None:
        return f"{name}={{{{ .{name} }}}}"
    return f"{name}={value}"

# Terraform variables
TF_VARS = [
    tf_var("databricks_account_id", "${DB_ACCOUNT_ID}"),
    tf_var("databricks_client_id", "${DB_ACCOUNT_CLIENT_ID}"),
    tf_var("workspace_name"),
    tf_var("databricks_client_secret", "${DB_ACCOUNT_CLIENT_SECRET}"),
]

# Git clone command
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'