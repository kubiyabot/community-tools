from kubiya_sdk.tools.models import FileSpec

# Common files needed for AWS access
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]

# Common environment variables - single source of truth
COMMON_ENV = [
    "AWS_PROFILE",      # AWS profile with required permissions
    "KUBIYA_USER_EMAIL" # User email for SSO lookup
] 