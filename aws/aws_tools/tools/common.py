from kubiya_sdk.tools import FileSpec


# Make sure you enable AWS integration on the Kubiya platform and that the TeamMate which is running this has the correct permissions to access AWS (is using an integration with AWS)
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="$HOME/.aws/credentials"),
]
