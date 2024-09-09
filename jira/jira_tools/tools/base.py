from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

class JiraTool(Tool):
    def __init__(self, name, description, content, args):
        super().__init__(
            name=name,
            description=description,
            type="python",
            content=content,
            args=args,
            env=["JIRA_OAUTH_TOKEN"],
        )

def register_jira_tool(tool):
    tool_registry.register("jira", tool)