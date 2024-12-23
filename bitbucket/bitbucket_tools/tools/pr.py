from kubiya_sdk.tools import Arg
from .base import BitbucketCliTool
from kubiya_sdk.tools.registry import tool_registry

pr_list = BitbucketCliTool(
    name="bitbucket_pr_list",
    description="List pull requests in a Bitbucket repository",
    content="""
    curl -s -u $BITBUCKET_AUTH \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pullrequests" | \
        jq '.values[] | {id, title, state, author: .author.display_name, created_on}'
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
    ],
)

pr_create = BitbucketCliTool(
    name="bitbucket_pr_create",
    description="Create a new pull request",
    content="""
    curl -X POST -u $BITBUCKET_AUTH \
        -H "Content-Type: application/json" \
        -d '{
            "title": "'$title'",
            "description": "'$description'",
            "source": {"branch": {"name": "'$source_branch'"}},
            "destination": {"branch": {"name": "'$destination_branch'"}}
        }' \
        "https://api.bitbucket.org/2.0/repositories/$workspace/$repo/pullrequests"
    """,
    args=[
        Arg(name="workspace", type="str", description="Bitbucket workspace slug", required=True),
        Arg(name="repo", type="str", description="Repository name", required=True),
        Arg(name="title", type="str", description="Pull request title", required=True),
        Arg(name="description", type="str", description="Pull request description", required=True),
        Arg(name="source_branch", type="str", description="Source branch name", required=True),
        Arg(name="destination_branch", type="str", description="Destination branch name", required=True),
    ],
)

# Register tools
for tool in [pr_list, pr_create]:
    tool_registry.register("bitbucket", tool)

__all__ = ['pr_list', 'pr_create'] 