from .base import BitbucketTool, register_bitbucket_tool
from kubiya_sdk.tools import Arg

pr_create = BitbucketTool(
    name="pr_create",
    description="Create a new Bitbucket pull request",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

pr = bitbucket.create_pull_request(
    workspace,
    repo_slug,
    title,
    source_branch,
    destination_branch,
    description
)
print(f"Created pull request: {pr['id']} - {pr['title']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="title", type="str", description="Pull request title", required=True),
        Arg(name="source_branch", type="str", description="Source branch", required=True),
        Arg(name="destination_branch", type="str", description="Destination branch", required=True),
        Arg(name="description", type="str", description="Pull request description", required=True),
    ],
)

pr_get = BitbucketTool(
    name="pr_get",
    description="Get Bitbucket pull request details",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

pr = bitbucket.get_pull_request(workspace, repo_slug, pr_id)
print(f"Pull request details: {pr}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="pr_id", type="int", description="Pull request ID", required=True),
    ],
)

pr_list = BitbucketTool(
    name="pr_list",
    description="List Bitbucket pull requests",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

prs = bitbucket.get_pull_requests(workspace, repo_slug)
for pr in prs:
    print(f"Pull request: {pr['id']} - {pr['title']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
    ],
)

pr_merge = BitbucketTool(
    name="pr_merge",
    description="Merge a Bitbucket pull request",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

result = bitbucket.merge_pull_request(workspace, repo_slug, pr_id)
print(f"Merged pull request: {result}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="pr_id", type="int", description="Pull request ID", required=True),
    ],
)

register_bitbucket_tool(pr_create)
register_bitbucket_tool(pr_get)
register_bitbucket_tool(pr_list)
register_bitbucket_tool(pr_merge)