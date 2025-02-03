from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_list = BitbucketCliTool(
    name="bitbucket_repo_list",
    description="List repositories in a Bitbucket workspace",
    content="""
    curl -s -u $BITBUCKET_AUTH \
        "https://api.bitbucket.org/2.0/repositories/$workspace" | \
        jq '.values[] | {name, full_name, description, updated_on}'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
    ],
)

repo_create = BitbucketCliTool(
    name="bitbucket_repo_create",
    description="Create a new Bitbucket repository",
    content="""
    curl -X POST -u $BITBUCKET_AUTH \
        -H "Content-Type: application/json" \
        -d '{
            "scm": "git",
            "is_private": '$([[ "$private" == "true" ]] && echo "true" || echo "false")',
            "name": "'$name'",
            "description": "'$description'"
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$name"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="name", type="str", description="Repository name", required=True),
        Arg(name="description", type="str", description="Repository description", required=False),
        Arg(name="private", type="bool", description="Whether the repository should be private", required=False),
    ],
)

# Register tools
for tool in [repo_list, repo_create]:
    tool_registry.register("bitbucket", tool)

__all__ = ['repo_list', 'repo_create'] 