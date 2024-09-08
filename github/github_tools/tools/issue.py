from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

issue_tool = GitHubCliTool(
    name="issue",
    description="Manages GitHub issues",
    content="""
    #!/bin/bash
    set -e
    gh issue $action $([[ -n "$number" ]] && echo "$number") $([[ -n "$title" ]] && echo "--title \"$title\"") $([[ -n "$body" ]] && echo "--body \"$body\"") $([[ -n "$repo" ]] && echo "--repo $repo")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, list, view, close, reopen)", required=True),
        Arg(name="number", type="str", description="Issue number", required=False),
        Arg(name="title", type="str", description="Issue title", required=False),
        Arg(name="body", type="str", description="Issue body", required=False),
        Arg(name="repo", type="str", description="Repository name", required=False),
    ],
)

tool_registry.register("github", issue_tool)