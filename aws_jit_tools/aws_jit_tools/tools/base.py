from kubiya_sdk.tools.models import Tool, FileSpec
from .common import COMMON_FILES, COMMON_ENV

AWS_ICON = "https://d2908q01vomqb2.cloudfront.net/22d200f8670dbdb3e253a90eee5098477c95c23d/2018/09/24/aws-icon-service-IAM_PERMISSIONS.png"

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools."""
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args=None,
        env=None,
        secrets=None,
        with_files=None,
        with_volumes=None,
        long_running=False,
        mermaid=None
    ):
        # Combine with common files and env
        files = list(COMMON_FILES)
        if with_files:
            files.extend(with_files)

        env_vars = list(COMMON_ENV)
        if env:
            env_vars.extend(env)

        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_ICON,
            type="docker",
            image="amazon/aws-cli:latest",
            content=f"""
#!/bin/bash
set -e

# Install required packages
apk add --no-cache python3 py3-pip
pip3 install boto3 requests

{content}
            """,
            args=args or [],
            env=env_vars,
            secrets=secrets or [],
            with_files=files,
            with_volumes=with_volumes,
            long_running=long_running,
            mermaid=mermaid
        )