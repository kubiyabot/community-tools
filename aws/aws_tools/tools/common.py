from kubiya_sdk.tools import FileSpec

COMMON_ENV = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
]

COMMON_FILES = [
    FileSpec(source="~/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="~/.aws/config", destination="/root/.aws/config"),
]