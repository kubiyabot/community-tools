from .base import BitbucketTool, register_bitbucket_tool
from kubiya_sdk.tools import Arg

repo_get = BitbucketTool(
    name="repo_get",
    description="Get Bitbucket repository details",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

repo = bitbucket.get_repo(workspace, repo_slug)
print(f"Repository details: {repo}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_slug", type="str", description="Repository slug", required=True),
    ],
)

repo_list = BitbucketTool(
    name="repo_list",
    description="List Bitbucket repositories",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

repos = bitbucket.get_repositories(workspace)
for repo in repos:
    print(f"Repository: {repo['name']} - {repo['full_name']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
    ],
)

repo_create = BitbucketTool(
    name="repo_create",
    description="Create a new Bitbucket repository",
    content="""
import os
from atlassian import Bitbucket

bitbucket = Bitbucket(
    url='https://api.bitbucket.org',
    username=os.environ['BITBUCKET_USERNAME'],
    password=os.environ['BITBUCKET_APP_PASSWORD']
)

new_repo = bitbucket.create_repo(workspace, repo_name, project_key)
print(f"Created repository: {new_repo['name']} - {new_repo['full_name']}")
    """,
    args=[
        Arg(name="workspace", type="str", description="Workspace name", required=True),
        Arg(name="repo_name", type="str", description="Repository name", required=True),
        Arg(name="project_key", type="str", description="Project key", required=True),
    ],
)

register_bitbucket_tool(repo_get)
register_bitbucket_tool(repo_list)
register_bitbucket_tool(repo_create)