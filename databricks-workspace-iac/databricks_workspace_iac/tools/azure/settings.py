# azure/settings.py

from databricks_workspace_iac.tools.shared_templates import (
    tf_var, GIT_CLONE_COMMAND, COMMON_WORKSPACE_TEMPLATE,
    WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING, ERROR_NOTIFICATION_TEMPLATE,
    generate_terraform_vars_json
)

from databricks_workspace_iac.tools.constants import DATABRICKS_ICON_URL

# Azure-specific settings for Databricks workspace creation

# Define Git repository details for Terraform configurations
GIT_REPO = 'databricks-workspace-iac'
TERRAFORM_MODULE_PATH = 'aux/databricks/terraform/azure'

# Define Terraform variables for Azure Databricks workspace
TF_VARS = [
    tf_var("WORKSPACE_NAME", "The name of the Databricks workspace to be created", required=True),
    tf_var("region", "The Azure region where the workspace will be deployed", required=True),
    tf_var("storage_account_name", "The name of the storage account to use for the backend", required=True),
    tf_var("container_name", "The name of the container to use for the backend", required=True),
    tf_var("resource_group_name", "The name of the resource group to use for the backend", required=True),
    # ... (include all other tf_vars as previously defined) ...
]

# Mermaid diagram for visualizing the workflow
MERMAID_DIAGRAM = """
flowchart TD
    %% User interaction
    User -->|🗨 Request Azure Databricks Workspace| Teammate
    Teammate -->|🗨 Which Resource Group and Location?| User
    User -->|📍 Resource Group: my-rg, Location: eastus| Teammate
    Teammate -->| Starting Azure Terraform Apply| ApplyAzure

    %% Azure Execution
    subgraph Azure Environment
        ApplyAzure[Azure Kubernetes Job]
        ApplyAzure -->|Running Terraform on Azure 🛠| K8sAzure[Checking Status 🔄]
        K8sAzure -->|⌛ Waiting for Completion| DatabricksAzure[Databricks Workspace Created 🎉]
        ApplyAzure -->|Uses| TerraformDockerAzure[Terraform Docker 🐳]
    end

    %% Feedback to User
    K8sAzure -->|✅ Success! Workspace Ready| Teammate
    Teammate -->|🎉 Workspace is ready!| User
"""

# List of required environment variables
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH",
    "ARM_CLIENT_ID", "ARM_CLIENT_SECRET", "ARM_TENANT_ID", "ARM_SUBSCRIPTION_ID",
    "PAT", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "SLACK_API_TOKEN"
]

# Generate the commands to check required variables
CHECK_REQUIRED_VARS_COMMANDS = '\n'.join([f'check_var "{var}"' for var in REQUIRED_ENV_VARS])

# Define Azure-specific parameters
AZURE_TEMPLATE_PARAMS = {
    "DATABRICKS_ICON_URL": DATABRICKS_ICON_URL,
    "CLOUD_PROVIDER": "Azure",
    "GIT_CLONE_COMMAND": GIT_CLONE_COMMAND,
    "TERRAFORM_MODULE_PATH": TERRAFORM_MODULE_PATH,
    "CHECK_REQUIRED_VARS": CHECK_REQUIRED_VARS_COMMANDS,
    "TERRAFORM_INIT_COMMAND": (
        'terraform init '
        '-backend-config="storage_account_name=${storage_account_name}" '
        '-backend-config="container_name=${container_name}" '
        '-backend-config="key=databricks/${WORKSPACE_NAME}/terraform.tfstate" '
        '-backend-config="resource_group_name=${resource_group_name}" '
        '-backend-config="subscription_id=$ARM_SUBSCRIPTION_ID"'
    ),
    "TERRAFORM_VARS_JSON": generate_terraform_vars_json(TF_VARS),
    "FALLBACK_WORKSPACE_URL": 'https://portal.azure.com/#@/resource/subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/${resource_group_name}/providers/Microsoft.Databricks/workspaces/${WORKSPACE_NAME}',
    "BACKEND_TYPE": "azurerm",
    "IMPORT_COMMAND": 'terraform import azurerm_databricks_workspace.this /subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/${resource_group_name}/providers/Microsoft.Databricks/workspaces/${WORKSPACE_NAME}',
    "GIT_REPO": GIT_REPO
}

# Generate the Azure-specific workspace template
AZURE_WORKSPACE_TEMPLATE = COMMON_WORKSPACE_TEMPLATE.format(**AZURE_TEMPLATE_PARAMS)

# Wrap the workspace template with error handling
AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING.format(
    WORKSPACE_TEMPLATE=AZURE_WORKSPACE_TEMPLATE,
    ERROR_NOTIFICATION_TEMPLATE=ERROR_NOTIFICATION_TEMPLATE.format(CLOUD_PROVIDER="Azure")
)
