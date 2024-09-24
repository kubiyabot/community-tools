from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

release_tool = GitHubCliTool(
    name="github_release",
    description="Manages GitHub releases",
    content="""
    #!/bin/bash
    set -e
    gh release $action $([[ -n "$tag" ]] && echo "$tag") $([[ -n "$title" ]] && echo "--title \"$title\"") $([[ -n "$notes" ]] && echo "--notes \"$notes\"") $([[ -n "$repo" ]] && echo "--repo $repo") $([[ -n "$options" ]] && echo "$options")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, list, view, delete)", required=True),
        Arg(name="tag", type="str", description="Release tag", required=False),
        Arg(name="title", type="str", description="Release title", required=False),
        Arg(name="notes", type="str", description="Release notes", required=False),
        Arg(name="repo", type="str", description="Repository name", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
    ],
)

tool_registry.register("github", release_tool)