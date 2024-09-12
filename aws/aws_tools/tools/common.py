from kubiya_sdk.tools.models import FileSpec

# Make sure you enable AWS integration on the Kubiya platform and that the TeamMate which is running this has the correct permissions to access AWS (is using an integration with AWS)
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]

# This is the profile that will be used to authenticate with AWS by default
# In a Kubiya managed teammate, this environment variable will be set automatically
# If you're using this in a local environment, make sure to set it on your shell
COMMON_ENV = [
    "AWS_PROFILE"
]