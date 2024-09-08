from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

workflow_tool = GitHubCliTool(
    name="github_workflow",
    description="Manages GitHub Actions workflows",
    content="""
    #!/bin/bash
    set -e
    gh workflow $action $([[ -n "$workflow" ]] && echo "$workflow") $([[ -n "$repo" ]] && echo "--repo $repo") $([[ -n "$options" ]] && echo "$options")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (list, view, run, disable, enable)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=False),
        Arg(name="repo", type="str", description="Repository name", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
    ],
)

tool_registry.register("github", workflow_tool)