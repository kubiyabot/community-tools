from kubiya_sdk.tools.models import Tool, FileSpec

AWS_JIT_ICON = "https://img.icons8.com/color/200/amazon-web-services.png"

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
    
    # Create AWS config directory and files for LocalStack
    mkdir -p /root/.aws
    cat > /root/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID:-test}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY:-test}
EOF
    
    cat > /root/.aws/config << EOF
[default]
region = ${AWS_DEFAULT_REGION:-us-east-1}
output = json
EOF
    
    echo ">> AWS credentials configured for LocalStack"
else
    export AWS_CLI_ENDPOINT_ARGS=""
fi

""" + content

        # Only include AWS credential files if not using LocalStack
        files_to_include = with_files or []
        if not env or "AWS_ENDPOINT_URL" not in (env or []):
            # Only add credential files for real AWS usage
            files_to_include.extend([
                FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
                FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
            ])

        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_JIT_ICON,
            type="docker",
            image="python:3.12-alpine",
            content=localstack_content,
            env=env or COMMON_ENV,
            with_files=files_to_include,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            args=args or []
        )

__all__ = ['AWSJITTool']