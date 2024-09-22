# azure/settings.py

from databricks_workspace_iac.tools.shared_templates import (
    tf_var,
    GIT_CLONE_COMMAND,
    COMMON_WORKSPACE_TEMPLATE,
    WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
    generate_terraform_vars_json,
    WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING,
)

from databricks_workspace_iac.tools.constants import DATABRICKS_ICON_URL

# Azure-specific settings for Databricks workspace creation using Terraform

# Do not forget to declare the variables in the executor (Kubiya team mate, or the Kubiya CLI)

# The GitHub organization containing the Terraform code for the Databricks workspace (name of the org)
GIT_ORG = "${GIT_ORG}"  # passed dynamically from the executor (Kubiya team mate, or the Kubiya CLI)

# The GitHub repository containing the Terraform code for the Databricks workspace (name of the repo)
GIT_REPO = "databricks-workspace-iac"

# The path to the Terraform module within the repository
TERRAFORM_MODULE_PATH = "aux/databricks/terraform/azure"

# Define Terraform variables for Azure Databricks workspace
# Each variable is created using the tf_var function, which sets name, description, required status, and default value
TF_VARS = [
    tf_var(
        "workspace_name",
        "The name of the Databricks workspace to be created",
        required=True,
    ),
    tf_var(
        "region", "The Azure region where the workspace will be deployed", required=True
    ),
    tf_var(
        "storage_account_name",
        "The name of the storage account to use for the backend",
        required=True,
    ),
    tf_var(
        "resource_group_name",
        "The name of the resource group to use for the backend",
        required=True,
    ),
    tf_var(
        "managed_services_cmk_key_vault_key_id",
        "The ID of the key vault key to use for managed services encryption",
        required=False,
    ),
    tf_var(
        "managed_disk_cmk_key_vault_key_id",
        "The ID of the key vault key to use for managed disk encryption",
        required=False,
    ),
    tf_var(
        "infrastructure_encryption_enabled",
        "Enable infrastructure encryption, can be true or false",
        required=False,
        default="false",
    ),
    tf_var(
        "no_public_ip",
        "Secure cluster connectivity, no public ip, can be true or false",
        required=False,
        default="false",
    ),
    tf_var(
        "enable_vnet",
        "Enable custom vnet use, boolean, can be true or false",
        required=False,
        default="false",
    ),
    tf_var("virtual_network_id", "The virtual network id", required=False),
    tf_var("private_subnet_name", "The name of the private subnet", required=False),
    tf_var("public_subnet_name", "The name of the public subnet", required=False),
    tf_var(
        "public_subnet_network_security_group_association_id",
        "The ID of the public subnet network security group association",
        required=False,
    ),
    tf_var(
        "private_subnet_network_security_group_association_id",
        "The ID of the private subnet network security group association",
        required=False,
    ),
    tf_var(
        "security_profile_enabled",
        "Enable security profile, boolean, can be true or false",
        required=False,
        default="false",
    ),
    tf_var(
        "enhanced_monitoring_enabled",
        "Enable enhanced monitoring, boolean, can be true or false",
        required=False,
        default="false",
    ),
    tf_var(
        "automatic_update", "Enable automatic update", required=False, default="false"
    ),
    tf_var(
        "restart_no_updates",
        "Enable restart even if there are no updates",
        required=False,
        default="false",
    ),
    tf_var("day_of_week", "Day of the week to apply updates", required=False),
    tf_var("frequency", "Frequency of updates", required=False),
    tf_var("hours", "Hours of window start time", required=False, default="1"),
    tf_var("minutes", "Minutes of window start time", required=False, default="0"),
    tf_var(
        "address_space",
        "The address space to be used for the virtual network",
        required=False,
        default='["10.0.0.0/16"]',
    ),
    tf_var(
        "address_prefixes_public",
        "The address prefix for the public network",
        required=False,
        default='["10.0.2.0/24"]',
    ),
    tf_var(
        "address_prefixes_private",
        "The address prefix for the private network",
        required=False,
        default='["10.0.1.0/24"]',
    ),
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

# List of required secrets
REQUIRED_SECRETS = [
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_TENANT_ID",
    "ARM_SUBSCRIPTION_ID",
    "PAT",
]

# List of required environment variables
REQUIRED_ENV_VARS = [
    # Azure-specific variables
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_TENANT_ID",
    "ARM_SUBSCRIPTION_ID",
    # Git-related variables
    "GIT_ORG",
    "GIT_REPO",
    "BRANCH",
    # Slack-related variables
    "SLACK_CHANNEL_ID",
    "SLACK_THREAD_TS",
    "SLACK_API_TOKEN",
    # Personal Access Token for GitHub (private repository authentication for the repository holding the terraform code)
    "PAT",
]

# Temporary hack to add secrets to the list of required environment variables
# TODO: Find a better way to handle this (fix agent manager to pass secrets to the tools)
REQUIRED_ENV_VARS = REQUIRED_ENV_VARS + REQUIRED_SECRETS

# Generate the commands to check required variables
CHECK_REQUIRED_VARS_COMMANDS = "\n".join(
    [f'check_var "{var}"' for var in REQUIRED_ENV_VARS]
)

# Define Azure-specific parameters
AZURE_TEMPLATE_PARAMS = {
    # URL for the Databricks icon, used for visual identification in UIs
    "DATABRICKS_ICON_URL": DATABRICKS_ICON_URL,
    # Specifies the cloud provider, used for cloud-specific logic
    "CLOUD_PROVIDER": "Azure",
    # Command to clone the Git repository containing Terraform configurations
    "GIT_CLONE_COMMAND": GIT_CLONE_COMMAND,
    # Path to the Terraform module within the cloned repository
    "TERRAFORM_MODULE_PATH": TERRAFORM_MODULE_PATH,
    # Commands to check for required environment variables
    "CHECK_REQUIRED_VARS": CHECK_REQUIRED_VARS_COMMANDS,
    # Terraform init command with Azure backend configuration
    # Double curly braces are used to interpolate variables in the command
    "TERRAFORM_INIT_COMMAND": 'terraform init -backend-config="storage_account_name=${{storage_account_name}}" -backend-config="container_name=${{container_name}}" -backend-config="key=databricks/${{WORKSPACE_NAME}}/terraform.tfstate" -backend-config="resource_group_name=${{resource_group_name}}" -backend-config="subscription_id=${{ARM_SUBSCRIPTION_ID}}"',
    # JSON representation of Terraform variables
    "TERRAFORM_VARS_JSON": generate_terraform_vars_json(TF_VARS),
    # Fallback URL for the Databricks workspace if direct URL is unavailable
    "FALLBACK_WORKSPACE_URL": "https://portal.azure.com/#@/resource/subscriptions/${{ARM_SUBSCRIPTION_ID}}/resourceGroups/${{resource_group_name}}/providers/Microsoft.Databricks/workspaces/${{WORKSPACE_NAME}}",
    # Specifies the backend type for Terraform state (azurerm for Azure)
    "BACKEND_TYPE": "azurerm",
    # Command to import existing Databricks workspace into Terraform state
    "IMPORT_COMMAND": "terraform import azurerm_databricks_workspace.this /subscriptions/${{ARM_SUBSCRIPTION_ID}}/resourceGroups/${{resource_group_name}}/providers/Microsoft.Databricks/workspaces/${{WORKSPACE_NAME}}",
    # Name of the Git repository containing the Terraform configurations
    "GIT_REPO": GIT_REPO,
}

# Generate the Azure-specific workspace template
AZURE_WORKSPACE_TEMPLATE = COMMON_WORKSPACE_TEMPLATE.render(**AZURE_TEMPLATE_PARAMS)

# Wrap the workspace template with error handling
AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = (
    WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING.format(
        WORKSPACE_TEMPLATE=AZURE_WORKSPACE_TEMPLATE,
        CLOUD_PROVIDER="Azure",
        TERRAFORM_MODULE_PATH=TERRAFORM_MODULE_PATH,
    )
)
