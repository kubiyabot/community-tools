from kubiya_sdk.tools.models import FileSpec

# Common environment variables used across all tools
COMMON_ENV = [
    "GIT_ORG",      # The GitHub Organization
    "GIT_REPO",     # The GitHub Repository
    "BRANCH",       # The branch to use
    "DIR",          # The directory to use
    "SLACK_CHANNEL_ID",  # The Slack Channel ID
    "SLACK_THREAD_TS",   # The Slack Thread Timestamp
]

# Common secrets used across all tools
COMMON_SECRETS = [
    "SLACK_API_TOKEN",  # The Slack API Token (Set via Team Mate settings -> Integrations -> Slack)
    "PAT",             # GitHub Personal Access Token for repository access
    "DB_ACCOUNT_ID",   # The Databricks Account ID
    "DB_ACCOUNT_CLIENT_ID",     # The Databricks Client ID
    "DB_ACCOUNT_CLIENT_SECRET", # The Databricks Client Secret
]

# AWS-specific environment variables
AWS_SPECIFIC_ENV = [
    "AWS_PROFILE",  # The AWS Profile to use
]

# AWS-specific secrets
AWS_SPECIFIC_SECRETS = [
    # Currently empty as all AWS secrets are common
]

# Azure-specific secrets
AZURE_SPECIFIC_SECRETS = [
    "ARM_CLIENT_ID",        # The ARM Client ID (Set via Team Mate settings)
    "ARM_CLIENT_SECRET",    # The ARM Client Secret (Set via Team Mate settings)
    "ARM_TENANT_ID",        # The ARM Tenant ID (Set via Team Mate settings)
    "ARM_SUBSCRIPTION_ID",  # The ARM Subscription ID
]

# Combine environment variables
AWS_ENV = COMMON_ENV + AWS_SPECIFIC_ENV
AZURE_ENV = COMMON_ENV  # Azure doesn't have specific env vars currently (only secrets)

# Combine secrets
AWS_SECRETS = COMMON_SECRETS + AWS_SPECIFIC_SECRETS
AZURE_SECRETS = COMMON_SECRETS + AZURE_SPECIFIC_SECRETS

# Icon URL
DATABRICKS_ICON_URL = "https://cledara-public.s3.eu-west-2.amazonaws.com/Databricks.png"

# AWS Files configuration
AWS_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),  # The AWS Credentials file
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),           # The AWS Config file
]