from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

# This module uses a custom docker image that has the jira-cli installed
# This custom image was designed to work with Kubiya
JIRA_DOCKER_IMAGE = "ghcr.io/kubiyabot/jira-cli:latest"


class JiraTool(Tool):
    def __init__(self, name, description, content, args, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image=JIRA_DOCKER_IMAGE,
            content=content,
            args=args,
            env=["JIRA_WORKSPACE_NAME"],
            secrets=["JIRA_OAUTH_TOKEN"],
            mermaid=mermaid_diagram
        )

#             uv pip install -r /tmp/requirements.txt > /dev/null 2>&1
class JiraPythonTool(Tool):
    def __init__(self, name, description, content, args, with_files=None, mermaid_diagram=None):
        if with_files is None:
            with_files = []
        super().__init__(
            name=name,
            description=description,
            image="python:3.12-slim",
            content=content,
            args=args,
            with_files=with_files,
            env=["JIRA_WORKSPACE_NAME"],
            secrets=["JIRA_OAUTH_TOKEN"],
            mermaid=mermaid_diagram
        )



def register_jira_tool(tool):
    tool_registry.register("jira", tool)