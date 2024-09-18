# Azure-specific settings
AZURE_TERRAFORM_DIR = '$DIR/aux/databricks/terraform/azure'

# Define a function to create Terraform variable strings
def tf_var(name, value=None):
    if value is None:
        return f"{name}={{{{ .{name} }}}}"
    return f"{name}={value}"

# Terraform variables
TF_VARS = [
    tf_var("WORKSPACE_NAME"),
    tf_var("region"),
    tf_var("managed_services_cmk_key_vault_key_id"),
    tf_var("managed_disk_cmk_key_vault_key_id"),
    tf_var("infrastructure_encryption_enabled"),
    tf_var("no_public_ip"),
    tf_var("enable_vnet"),
    tf_var("virtual_network_id"),
    tf_var("private_subnet_name"),
    tf_var("public_subnet_name"),
    tf_var("public_subnet_network_security_group_association_id"),
    tf_var("private_subnet_network_security_group_association_id"),
    tf_var("storage_account_name"),
    tf_var("security_profile_enabled"),
    tf_var("enhanced_monitoring_enabled"),
    tf_var("azure_client_id", "${ARM_CLIENT_ID}"),
    tf_var("azure_client_secret", "${ARM_CLIENT_SECRET}"),
    tf_var("azure_tenant_id", "${ARM_TENANT_ID}"),
    tf_var("automatic_update"),
    tf_var("restart_no_updates"),
    tf_var("day_of_week"),
    tf_var("frequency"),
    tf_var("hours"),
    tf_var("minutes"),
    tf_var("address_space"),
    tf_var("address_prefixes_public"),
    tf_var("address_prefixes_private"),
]

# Git clone command
GIT_CLONE_COMMAND = 'git clone -b "$BRANCH" https://"$PAT"@github.com/"$GIT_ORG"/"$GIT_REPO".git $DIR'