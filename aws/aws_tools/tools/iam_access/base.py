from kubiya_sdk.tools.models import Tool
from typing import Dict, Any, List

AWS_IAM_ICON = "https://d2908q01vomqb2.cloudfront.net/22d200f8670dbdb3e253a90eee5098477c95c23d/2018/09/24/aws-icon-service-IAM_PERMISSIONS.png"

class AWSIAMAccessTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Any] = None,
        env: List[str] = None,
        secrets: List[str] = None,
        long_running: bool = False,
        with_files: List[Any] = None,
        mermaid: str = None
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_IAM_ICON,
            type="python",
            content=content,
            args=args or [],
            env=env or ["AWS_PROFILE", "KUBIYA_USER_EMAIL"],
            secrets=secrets or [],
            requirements=["boto3", "pyyaml", "requests"],
            with_files=with_files,
            long_running=long_running,
            mermaid=mermaid
        ) 