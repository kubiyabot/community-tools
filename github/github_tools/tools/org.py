from kubiya_sdk.tools import Arg
from .base import GitHubRepolessCliTool
from kubiya_sdk.tools.registry import tool_registry

get_org_members = GitHubRepolessCliTool(
    name="get_org_members",
    description="Get a list of all org's users.",
    content="gh api orgs/$org/members?per_page=100 --paginate --slurp",
    args=[
        Arg(name="org", type="str", description="The github organization name. Example: 'octocat'", required=True),
    ],
)

# Register all org tools
for tool in [get_org_members]:
    tool_registry.register("github", tool)

# Export all org tools
__all__ = ['get_org_members']
