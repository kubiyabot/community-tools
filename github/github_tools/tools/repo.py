from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_tool = GitHubCliTool(
    name="repo",
    description="Comprehensive GitHub repository management",
    content="""
    #!/bin/bash
    set -e
    case "$action" in
        create)
            gh repo create $name $([[ "$private" == "true" ]] && echo "--private" || echo "--public") $([[ -n "$description" ]] && echo "--description \"$description\"") $([[ -n "$homepage" ]] && echo "--homepage $homepage")
            ;;
        clone)
            gh repo clone $repo
            ;;
        view)
            gh repo view $repo $([[ "$web" == "true" ]] && echo "--web")
            ;;
        list)
            gh repo list $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$visibility" ]] && echo "--$visibility")
            ;;
        delete)
            gh repo delete $repo --yes
            ;;
        fork)
            gh repo fork $repo $([[ "$clone" == "true" ]] && echo "--clone")
            ;;
        archive)
            gh repo archive $repo --yes
            ;;
        unarchive)
            gh repo unarchive $repo --yes
            ;;
        rename)
            gh repo rename $repo $new_name
            ;;
        *)
            echo "Invalid action"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform", required=True),
        Arg(name="repo", type="str", description="Repository name or URL", required=False),
        Arg(name="name", type="str", description="New repository name", required=False),
        Arg(name="private", type="bool", description="Create as private repository", required=False),
        Arg(name="description", type="str", description="Repository description", required=False),
        Arg(name="homepage", type="str", description="Repository homepage URL", required=False),
        Arg(name="web", type="bool", description="Open in web browser", required=False),
        Arg(name="limit", type="int", description="Number of repositories to list", required=False),
        Arg(name="visibility", type="str", description="Repository visibility (public/private)", required=False),
        Arg(name="clone", type="bool", description="Clone after forking", required=False),
        Arg(name="new_name", type="str", description="New name for repository", required=False),
    ],
)

tool_registry.register("github", repo_tool)