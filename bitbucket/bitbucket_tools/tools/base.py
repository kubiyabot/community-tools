from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

class BitbucketTool(Tool):
    def __init__(self, name, description, content, args):
        super().__init__(
            name=name,
            description=description,
            type="python",
            content=content,
            args=args,
            env=["BITBUCKET_USERNAME", "BITBUCKET_APP_PASSWORD"],
        )

def register_bitbucket_tool(tool):
    tool_registry.register("bitbucket", tool)