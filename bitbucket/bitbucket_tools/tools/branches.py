from .base import BitbucketTool, register_bitbucket_tool
from kubiya_sdk.tools import Arg

branch_create = BitbucketTool(
    name="branch_create",
    description="Create a new Bitbucket branch",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

result = bitbucket.create_branch(workspace, repo_slug, branch_name, start_point)
print(f"Created branch: {result}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="branch_name", type="str", description="New branch name", required=True),
        Arg(name="start_point", type="str", description="Starting point (commit hash or branch name)", required=True),
    ],
)

branch_delete = BitbucketTool(
    name="branch_delete",
    description="Delete a Bitbucket branch",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

result = bitbucket.delete_branch(workspace, repo_slug, branch_name)
print(f"Deleted branch: {result}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="branch_name", type="str", description="Branch name to delete", required=True),
    ],
)

branch_list = BitbucketTool(
    name="branch_list",
    description="List Bitbucket branches",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

branches = bitbucket.get_branches(workspace, repo_slug)
for branch in branches:
    print(f"Branch: {branch['name']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
    ],
)

register_bitbucket_tool(branch_create)
register_bitbucket_tool(branch_delete)
register_bitbucket_tool(branch_list)