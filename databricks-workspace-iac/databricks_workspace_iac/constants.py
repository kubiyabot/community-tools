from kubiya_sdk.tools.models import FileSpec

AWS_ENV = [
    "DB_ACCOUNT_ID",
    "DB_ACCOUNT_CLIENT_ID",
    "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG",
    "GIT_REPO",
    "BRANCH",
    "DIR",
    "PAT",
    "AWS_PROFILE"
]

AZURE_ENV = [
    "DB_ACCOUNT_ID",
    "DB_ACCOUNT_CLIENT_ID",
    "DB_ACCOUNT_CLIENT_SECRET",
    "GIT_ORG",
    "GIT_REPO",
    "BRANCH",
    "DIR",
    "PAT",
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_TENANT_ID",
    "ARM_SUBSCRIPTION_ID",
    "SLACK_CHANNEL_ID",
    "SLACK_THREAD_TS",
    "SLACK_API_TOKEN"
]

DATABRICKS_ICON_URL = "https://www.databricks.com/wp-content/uploads/2020/04/databricks-logo-1.png"

AWS_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]