from kubiya_sdk.tools.models import FileSpec

AWS_ENV = [
    "DB_ACCOUNT_ID", # The Databricks Account ID
    "DB_ACCOUNT_CLIENT_ID", # The Databricks Client ID
    "DB_ACCOUNT_CLIENT_SECRET", # The Databricks Client Secret
    "GIT_ORG", # The GitHub Organization
    "GIT_REPO", # The GitHub Repository
    "BRANCH", # The branch to use
    "DIR", # The directory to use
    "PAT", # The PAT to use
    "AWS_PROFILE", # The AWS Profile to use
    "SLACK_CHANNEL_ID", # The Slack Channel ID
    "SLACK_THREAD_TS", # The Slack Thread Timestamp
    "SLACK_API_TOKEN" # The Slack API Token
]

AZURE_ENV = [
    "DB_ACCOUNT_ID",
    "DB_ACCOUNT_CLIENT_ID", # The Databricks Client ID
    "DB_ACCOUNT_CLIENT_SECRET", # The Databricks Client Secret
    "GIT_ORG", # The GitHub Organization
    "GIT_REPO", # The GitHub Repository
    "BRANCH", # The branch to use
    "DIR", # The directory to use
    "PAT", # The PAT to use
    "ARM_CLIENT_ID", # The ARM Client ID (Set via Team Mate settings)
    "ARM_CLIENT_SECRET", # The ARM Client Secret (Set via Team Mate settings)
    "ARM_TENANT_ID", # The ARM Tenant ID (Set via Team Mate settings)
    "ARM_SUBSCRIPTION_ID", # The ARM Subscription ID
    "SLACK_CHANNEL_ID", # The Slack Channel ID
    "SLACK_THREAD_TS", # The Slack Thread Timestamp
    "SLACK_API_TOKEN" # The Slack API Token
]

DATABRICKS_ICON_URL = "https://cledara-public.s3.eu-west-2.amazonaws.com/Databricks.png"

AWS_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"), # The AWS Credentials file - must be set to the location of the AWS credentials file on the host machine
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"), # The AWS Config file - must be set to the location of the AWS config file on the host machine
]