from kubiya_sdk.tools.models import Tool
from .common import COMMON_FILES, COMMON_ENV

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

class AWSCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_ICON_URL,
            type="docker",
            image="amazon/aws-cli:latest",
            content=content,
            args=args,
            with_files=COMMON_FILES,
            env=COMMON_ENV,
            long_running=long_running,
            mermaid_diagram=mermaid_diagram
        )

class AWSSdkTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_ICON_URL,
            type="python",
            content=content,
            args=args,
            requirements=["boto3"],
            with_files=COMMON_FILES,
            env=COMMON_ENV,
            long_running=long_running,
            mermaid=mermaid_diagram
        )
