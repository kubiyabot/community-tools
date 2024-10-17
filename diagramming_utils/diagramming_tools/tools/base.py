from kubiya_sdk.tools import Tool

MERMAID_ICON_URL = "https://mermaid.js.org/favicon.svg"

class DiagrammingTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        mermaid_setup = """
        #!/bin/bash
        set -e
        npm install @mermaid-js/mermaid-cli
        """
        modified_content = mermaid_setup + "\n" + content
        super().__init__(
            name=name,
            description=description,
            icon_url=MERMAID_ICON_URL,
            type="docker",
            image="node:14-slim",
            content=modified_content,
            args=args,
            long_running=long_running,
        )
