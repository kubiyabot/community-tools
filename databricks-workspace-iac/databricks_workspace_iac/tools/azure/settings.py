# Azure-specific settings
AZURE_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/azure'

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
    tf_var("region", "The Azure region where the workspace will be deployed", required=True),
    tf_var("storage_account_name", "The name of the storage account to use for the backend", required=True),
    tf_var("container_name", "The name of the container to use for the backend", required=True),
    tf_var("resource_group_name", "The name of the resource group to use for the backend", required=True),
    tf_var("managed_services_cmk_key_vault_key_id", "The ID of the key vault key to use for managed services encryption"),
    tf_var("managed_disk_cmk_key_vault_key_id", "The ID of the key vault key to use for managed disk encryption"),
    tf_var("infrastructure_encryption_enabled", "Enable infrastructure encryption, can be true or false", default=False),
    tf_var("no_public_ip", "Secure cluster connectivity, no public ip, can be true or false", default=False),
    tf_var("enable_vnet", "Enable custom vnet use, boolean, can be true or false", default=False),
    tf_var("virtual_network_id", "The virtual network id"),
    tf_var("private_subnet_name", "The name of the private subnet"),
    tf_var("public_subnet_name", "The name of the public subnet"),
    tf_var("public_subnet_network_security_group_association_id", "The ID of the public subnet network security group association"),
    tf_var("private_subnet_network_security_group_association_id", "The ID of the private subnet network security group association"),
    tf_var("security_profile_enabled", "Enable security profile, boolean, can be true or false", default=False),
    tf_var("enhanced_monitoring_enabled", "Enable enhanced monitoring, boolean, can be true or false", default=False),
    tf_var("azure_client_id", "Azure client ID", default="${ARM_CLIENT_ID}"),
    tf_var("azure_client_secret", "Azure client secret", default="${ARM_CLIENT_SECRET}"),
    tf_var("azure_tenant_id", "Azure tenant ID", default="${ARM_TENANT_ID}"),
    tf_var("automatic_update", "Enable automatic update", default=False),
    tf_var("restart_no_updates", "Enable restart even if there are no updates", default=False),
    tf_var("day_of_week", "Day of the week to apply updates"),
    tf_var("frequency", "Frequency of updates"),
    tf_var("hours", "Hours of window start time", default="1"),
    tf_var("minutes", "Minutes of window start time", default="0"),
    tf_var("address_space", "The address space to be used for the virtual network", default='["10.0.0.0/16"]'),
    tf_var("address_prefixes_public", "The address prefix for the public network", default='["10.0.2.0/24"]'),
    tf_var("address_prefixes_private", "The address prefix for the private network", default='["10.0.1.0/24"]'),
]

# Git clone command
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'