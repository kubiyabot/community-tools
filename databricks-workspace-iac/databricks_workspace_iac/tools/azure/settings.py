import json
from databricks_workspace_iac.tools.constants import DATABRICKS_ICON_URL
from databricks_workspace_iac.tools.shared_templates import (
    tf_var, GIT_CLONE_COMMAND, COMMON_WORKSPACE_TEMPLATE, 
    WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING, ERROR_NOTIFICATION_TEMPLATE, 
    generate_terraform_vars_json
)

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
    tf_var("managed_services_cmk_key_vault_key_id", "The ID of the key vault key to use for managed services encryption", required=False),
    tf_var("managed_disk_cmk_key_vault_key_id", "The ID of the key vault key to use for managed disk encryption", required=False),
    tf_var("infrastructure_encryption_enabled", "Enable infrastructure encryption, can be true or false", required=False, default="false"),
    tf_var("no_public_ip", "Secure cluster connectivity, no public ip, can be true or false", required=False, default="false"),
    tf_var("enable_vnet", "Enable custom vnet use, boolean, can be true or false", required=False, default="false"),
    tf_var("virtual_network_id", "The virtual network id", required=False),
    tf_var("private_subnet_name", "The name of the private subnet", required=False),
    tf_var("public_subnet_name", "The name of the public subnet", required=False),
    tf_var("public_subnet_network_security_group_association_id", "The ID of the public subnet network security group association", required=False),
    tf_var("private_subnet_network_security_group_association_id", "The ID of the private subnet network security group association", required=False),
    tf_var("security_profile_enabled", "Enable security profile, boolean, can be true or false", required=False, default="false"),
    tf_var("enhanced_monitoring_enabled", "Enable enhanced monitoring, boolean, can be true or false", required=False, default="false"),
    tf_var("azure_client_id", "Azure client ID", required=False, default="${ARM_CLIENT_ID}"),
    tf_var("azure_client_secret", "Azure client secret", required=False, default="${ARM_CLIENT_SECRET}"),
    tf_var("azure_tenant_id", "Azure tenant ID", required=False, default="${ARM_TENANT_ID}"),
    tf_var("automatic_update", "Enable automatic update", required=False, default="false"),
    tf_var("restart_no_updates", "Enable restart even if there are no updates", required=False, default="false"),
    tf_var("day_of_week", "Day of the week to apply updates", required=False),
    tf_var("frequency", "Frequency of updates", required=False),
    tf_var("hours", "Hours of window start time", required=False, default="1"),
    tf_var("minutes", "Minutes of window start time", required=False, default="0"),
    tf_var("address_space", "The address space to be used for the virtual network", required=False, default='["10.0.0.0/16"]'),
    tf_var("address_prefixes_public", "The address prefix for the public network", required=False, default='["10.0.2.0/24"]'),
    tf_var("address_prefixes_private", "The address prefix for the private network", required=False, default='["10.0.1.0/24"]'),
]

# List of required environment variables
REQUIRED_ENV_VARS = [
    "DB_ACCOUNT_ID", "DB_ACCOUNT_CLIENT_ID", "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG", "GIT_REPO", "BRANCH",
    "ARM_CLIENT_ID", "ARM_CLIENT_SECRET", "ARM_TENANT_ID", "ARM_SUBSCRIPTION_ID",
    "PAT", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", "SLACK_API_TOKEN"
]

# Define Azure-specific parameters
AZURE_TEMPLATE_PARAMS = {
    "CLOUD_PROVIDER": "Azure",
    "CHECK_REQUIRED_VARS": ' '.join(REQUIRED_ENV_VARS),
    "TERRAFORM_INIT_COMMAND": (
        'terraform init -backend-config="storage_account_name={{ .storage_account_name}}" '
        '-backend-config="container_name={{ .container_name}}" '
        '-backend-config="key=databricks/{{ .WORKSPACE_NAME}}/terraform.tfstate" '
        '-backend-config="resource_group_name={{ .resource_group_name}}" '
        '-backend-config="subscription_id=$ARM_SUBSCRIPTION_ID"'
    ),
    "TERRAFORM_VARS_JSON": generate_terraform_vars_json(TF_VARS),
    "FALLBACK_WORKSPACE_URL": "https://portal.azure.com/#@/resource/subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/$resource_group_name/providers/Microsoft.Databricks/workspaces/$workspace_name",
    "BACKEND_TYPE": "azurerm",
    "IMPORT_COMMAND": "terraform import azurerm_databricks_workspace.this /subscriptions/$ARM_SUBSCRIPTION_ID/resourceGroups/$resource_group_name/providers/Microsoft.Databricks/workspaces/$workspace_name",
    "GIT_CLONE_COMMAND": GIT_CLONE_COMMAND,
    "TERRAFORM_MODULE_PATH": TERRAFORM_MODULE_PATH,
    "GIT_REPO": GIT_REPO
}

# Generate the Azure-specific workspace template
AZURE_WORKSPACE_TEMPLATE = COMMON_WORKSPACE_TEMPLATE.format(**AZURE_TEMPLATE_PARAMS)

# Wrap the workspace template with error handling
AZURE_WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING = WORKSPACE_TEMPLATE_WITH_ERROR_HANDLING.format(
    WORKSPACE_TEMPLATE=AZURE_WORKSPACE_TEMPLATE,
    ERROR_NOTIFICATION_TEMPLATE=ERROR_NOTIFICATION_TEMPLATE.format(CLOUD_PROVIDER="Azure")
)
