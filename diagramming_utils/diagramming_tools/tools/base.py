from kubiya_sdk.tools import Tool, Arg, FileSpec

MERMAID_ICON_URL = "https://mermaid.js.org/favicon.svg"

class DiagrammingTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        super().__init__(
            name=name,
            description=description,
            icon_url=MERMAID_ICON_URL,
            type="docker",
            image="minlag/mermaid-cli:latest",
            content=content,
            args=args,
            long_running=long_running,
        )
