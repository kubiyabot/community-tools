from kubiya_sdk.tools.models import Tool
from .common import COMMON_FILES, COMMON_ENV

AWS_JIT_ICON = "https://d2908q01vomqb2.cloudfront.net/22d200f8670dbdb3e253a90eee5098477c95c23d/2018/09/24/aws-icon-service-IAM_PERMISSIONS.png"

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools."""
    def __init__(
        self, 
        name: str, 
        description: str, 
        content: str,
        env: list = None,
        long_running: bool = False,
        mermaid: str = None
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_JIT_ICON,
            type="docker",
            image="amazon/aws-cli:latest",
            content=content,
            env=env or COMMON_ENV,
            with_files=COMMON_FILES,
            long_running=long_running,
            mermaid=mermaid
        )

__all__ = ['AWSJITTool']