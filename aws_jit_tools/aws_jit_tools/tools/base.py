from kubiya_sdk.tools.models import Tool, FileSpec

AWS_JIT_ICON = "https://img.icons8.com/color/200/amazon-web-services.png"

# Common files needed for AWS access
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]

# Common environment variables - added LocalStack support
COMMON_ENV = [
    "AWS_ENDPOINT_URL",  # Added for LocalStack support
    "AWS_ACCESS_KEY_ID",  # Added for LocalStack support
    "AWS_SECRET_ACCESS_KEY",  # Added for LocalStack support
    "AWS_DEFAULT_REGION",  # Added for LocalStack support
    "KUBIYA_USER_EMAIL",
    "SLACK_CHANNEL_ID",
    "SLACK_THREAD_TS",
]

# Common secrets
COMMON_SECRETS = ["SLACK_API_TOKEN"]

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools with LocalStack support."""
    def __init__(
        self, 
        name: str, 
        description: str, 
        content: str,
        env: list = None,
        # Default to long running to ensure the tool is always available
        # As the tools are waiting for the TTL to expire before revoking access
        # This is to avoid race conditions where the tool is not available when the TTL expires
        long_running: bool = False,
        mermaid: str = None,
        with_files: list = None,
        args: list = None
    ):
        # Add LocalStack configuration to the content
        localstack_content = """#!/bin/bash
set -e

# Configure LocalStack endpoint if provided
if [ -n "$AWS_ENDPOINT_URL" ]; then
    echo ">> Configuring for LocalStack endpoint: $AWS_ENDPOINT_URL"
    export AWS_CLI_ENDPOINT_ARGS="--endpoint-url $AWS_ENDPOINT_URL"
else
    export AWS_CLI_ENDPOINT_ARGS=""
fi

""" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_JIT_ICON,
            type="docker",
            image="python:3.12-alpine",
            content=localstack_content,
            env=env or COMMON_ENV,
            with_files=(with_files or []) + COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            args=args or []
        )

__all__ = ['AWSJITTool']