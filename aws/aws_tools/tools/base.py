from kubiya_sdk.tools import Tool
from .common import COMMON_ENV, COMMON_FILES

class AWSCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        super().__init__(
            name=name,
            description=description,
            type="container",
            image="amazon/aws-cli:latest",
            content=content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            long_running=long_running
        )

class AWSSdkTool(Tool):
    def __init__(self, name, description, content, args):
        super().__init__(
            name=name,
            description=description,
            type="python",
            content=content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
        )