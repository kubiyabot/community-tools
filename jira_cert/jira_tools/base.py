from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry

class JiraCertTool(Tool):
    def __init__(self, name, description, content, args, with_files=None, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="python:3.12-slim",
            on_build="""
pip install requests > /dev/null
pip install kubiya-sdk > /dev/null
            """,
            content=content,
            args=args,
            env=["JIRA_SERVER_URL", "KUBIYA_USER_EMAIL"],
            secrets=["JIRA_CLIENT_CERT", "JIRA_CLIENT_KEY", "JIRA_USER_CREDS"],
            with_files=with_files if with_files else [],
            mermaid=mermaid_diagram,
            icon_url="https://logos-world.net/wp-content/uploads/2021/02/Jira-Emblem.png",
        )

def register_jira_tool(tool):
    tool_registry.register("jira_cert", tool)