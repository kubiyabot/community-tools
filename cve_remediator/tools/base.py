from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry

class CVETool(Tool):
    def __init__(self, name, description, content, args, with_files=None, mermaid_diagram=None):
        if with_files is None:
            with_files = []
        super().__init__(
            name=name,
            description=description,
            image="python:3.12-slim",
            on_build="""
pip install requests > /dev/null
            """,
            content=content,
            args=args,
            with_files=with_files,
            mermaid=mermaid_diagram,
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/NIST_logo.svg/1200px-NIST_logo.svg.png",
        )

def register_cve_tool(tool):
    tool_registry.register("cve", tool) 