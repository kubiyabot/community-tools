from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

branch_list = BitbucketCliTool(
    name="bitbucket_branch_list",
    description="List branches in a Bitbucket repository",
    content="""
    curl -s -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/refs/branches" | \
        jq '.values[] | {name, target: {hash: .target.hash, date: .target.date}}'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
    ],
)

branch_create = BitbucketCliTool(
    name="bitbucket_branch_create",
    description="Create a new branch in a Bitbucket repository",
    content="""
    curl -X POST -H "$BITBUCKET_AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "'$branch_name'",
            "target": {
                "hash": "'$source_commit'"
            }
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/refs/branches"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="branch_name", type="str", description="Name for the new branch", required=True),
        Arg(name="source_commit", type="str", description="Commit hash to create branch from", required=True),
    ],
)

branch_delete = BitbucketCliTool(
    name="bitbucket_branch_delete",
    description="Delete a branch from a Bitbucket repository",
    content="""
    curl -X DELETE -H "$BITBUCKET_AUTH_HEADER" \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/refs/branches/$branch_name"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="branch_name", type="str", description="Name of the branch to delete", required=True),
    ],
)

# Register tools
for tool in [branch_list, branch_create, branch_delete]:
    tool_registry.register("bitbucket", tool)

__all__ = ['branch_list', 'branch_create', 'branch_delete']