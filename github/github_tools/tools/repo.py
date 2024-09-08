from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_tool = GitHubCliTool(
    name="github_repo",
    description="Manages GitHub repositories",
    content="""
    #!/bin/bash
    set -e
    gh repo $action $([[ -n "$repo" ]] && echo "$repo") $([[ -n "$options" ]] && echo "$options")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, clone, view, list, delete)", required=True),
        Arg(name="repo", type="str", description="Repository name or URL", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
    ],
)

tool_registry.register("github", repo_tool)