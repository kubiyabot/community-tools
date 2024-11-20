from kubiya_sdk.tools.models import Tool, FileSpec

AWS_JIT_ICON = "https://img.icons8.com/color/200/amazon-web-services.png"

# Common files needed for AWS access
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]

# Common environment variables
COMMON_ENV = [
    "AWS_PROFILE",
    "KUBIYA_USER_EMAIL",
    "SLACK_CHANNEL_ID",
    "SLACK_THREAD_TS",
]

# Common secrets
COMMON_SECRETS = ["SLACK_API_TOKEN"]

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools."""
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
        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_JIT_ICON,
            type="docker",
            image="python:3.12-alpine",
            content=content,
            env=env or COMMON_ENV,
            with_files=(with_files or []) + COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            args=args or []
        )

__all__ = ['AWSJITTool']