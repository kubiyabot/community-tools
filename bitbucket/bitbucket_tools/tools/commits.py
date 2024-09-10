from .base import BitbucketTool, register_bitbucket_tool
from kubiya_sdk.tools import Arg

commit_get = BitbucketTool(
    name="commit_get",
    description="Get Bitbucket commit details",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

commit = bitbucket.get_commit(workspace, repo_slug, commit_hash)
print(f"Commit details: {commit}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="commit_hash", type="str", description="Commit hash", required=True),
    ],
)

commit_list = BitbucketTool(
    name="commit_list",
    description="List Bitbucket commits",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

commits = bitbucket.get_commits(workspace, repo_slug, branch=branch)
for commit in commits:
    print(f"Commit: {commit['hash']} - {commit['message']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
        Arg(name="branch", type="str", description="Branch name", required=True),
    ],
)

register_bitbucket_tool(commit_get)
register_bitbucket_tool(commit_list)