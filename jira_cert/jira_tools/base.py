import os
from kubiya_sdk.tools import Tool, Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry

class JiraCertTool(Tool):
    def __init__(self, name, description, content, args, with_files=None, mermaid_diagram=None):
        # Get certificate and key content from environment variables
        CLIENT_CERT = os.getenv("JIRA_CLIENT_CERT")
        CLIENT_KEY = os.getenv("JIRA_CLIENT_KEY")

        if not CLIENT_CERT or not CLIENT_KEY:
            raise ValueError("JIRA_CLIENT_CERT and JIRA_CLIENT_KEY environment variables must be set")

        # Create temporary paths for the cert files
        cert_path = "/tmp/jira_client.crt"
        key_path = "/tmp/jira_client.key"

        # Combine cert files with any tool-specific files
        cert_files = [
            FileSpec(destination=cert_path, content=CLIENT_CERT),
            FileSpec(destination=key_path, content=CLIENT_KEY)
        ]
        if with_files:
            cert_files.extend(with_files)

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
            env=["JIRA_SERVER_URL"],
            secrets=["JIRA_CLIENT_CERT", "JIRA_CLIENT_KEY"],
            with_files=cert_files,
            mermaid=mermaid_diagram,
            icon_url="https://logos-world.net/wp-content/uploads/2021/02/Jira-Emblem.png",
        )

def register_jira_tool(tool):
    tool_registry.register("jira_cert", tool)