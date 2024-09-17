def generate_terraform_vars(config):
    return " ".join([f"-var '{k}={v}'" for k, v in vars(config).items() if v is not None])

def generate_backend_config(config):
    return " ".join([
        f"-backend-config='storage_account_name={config.storage_account_name}'",
        f"-backend-config='container_name={config.container_name}'",
        f"-backend-config='key=databricks/{config.workspace_name}/terraform.tfstate'",
        f"-backend-config='resource_group_name={config.resource_group_name}'",
        "-backend-config='subscription_id=${ARM_SUBSCRIPTION_ID}'"
    ])