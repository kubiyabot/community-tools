from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

pr_tool = GitHubCliTool(
    name="github_pr",
    description="Manages GitHub pull requests",
    content="""
    #!/bin/bash
    set -e
    gh pr $action $([[ -n "$number" ]] && echo "$number") $([[ -n "$title" ]] && echo "--title \"$title\"") $([[ -n "$body" ]] && echo "--body \"$body\"") $([[ -n "$base" ]] && echo "--base $base") $([[ -n "$head" ]] && echo "--head $head") $([[ -n "$repo" ]] && echo "--repo $repo")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, list, view, checkout, merge, close)", required=True),
        Arg(name="number", type="str", description="PR number", required=False),
        Arg(name="title", type="str", description="PR title", required=False),
        Arg(name="body", type="str", description="PR body", required=False),
        Arg(name="base", type="str", description="Base branch", required=False),
        Arg(name="head", type="str", description="Head branch", required=False),
        Arg(name="repo", type="str", description="Repository name", required=False),
    ],
)

tool_registry.register("github", pr_tool)