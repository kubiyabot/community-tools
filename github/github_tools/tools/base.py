from kubiya_sdk.tools import Tool, FileSpec
from kubiya_sdk.tools import Arg, Volume
from kubiya_sdk.tools.registry import tool_registry
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"
GITHUB_CLI_DOCKER_IMAGE = "maniator/gh:latest"

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, with_volumes=None):      
        if with_volumes is None:
            with_volumes = []
            
        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image=GITHUB_CLI_DOCKER_IMAGE,
            content=content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            with_volumes=with_volumes
        )


class GitHubRepolessCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, with_volumes=None):
        if with_volumes is None:
            with_volumes = []
            
        enhanced_content = f"""
#!/bin/sh
set -e

if ! command -v jq >/dev/null 2>&1; then
    # Silently install jq and git
    apk add --quiet jq git >/dev/null 2>&1
fi

check_and_set_org() {{
    if [ -n "$org" ]; then
        echo "Using organization: $org"
    else
        orgs=$(gh api user/orgs --jq '.[].login')
        org_count=$(echo "$orgs" | wc -l)
        if [ "$org_count" -eq 0 ]; then
            echo "You are not part of any organization."
        elif [ "$org_count" -eq 1 ]; then
            org=$orgs
            echo "You are part of one organization: $org. Using this organization."
        else
            echo "You are part of the following organizations:"
            echo "$orgs"
            echo "Please specify the organization in your command if needed."
        fi
    fi
}}
check_and_set_org

{content}
"""

        updated_args = [arg for arg in args if arg.name not in ["org", "repo"]]
        updated_args.extend([
            Arg(name="org", type="str", description="GitHub organization name. If you're a member of only one org, it will be used automatically.", required=False),
        ])

        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image=GITHUB_CLI_DOCKER_IMAGE,
            content=enhanced_content,
            args=updated_args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            with_volumes=with_volumes
        )

# Define stream_workflow_logs tool
stream_workflow_logs = GitHubCliTool(
    name="github_stream_workflow_logs",
    description="Stream logs from a GitHub Actions workflow run in real-time.",
    content="""
#!/bin/sh
set -e

if [ -z "$run_id" ]; then
    echo "No run ID provided. Fetching the latest workflow run..."
    run_id=$(gh run list --repo $repo --limit 1 --json databaseId --jq '.[0].databaseId')
    if [ -z "$run_id" ]; then
        echo "No workflow runs found for the repository."
        exit 1
    fi
    echo "Using the latest run ID: $run_id"
fi

echo "Streaming logs for workflow run $run_id in repository $repo..."
gh run view $run_id --repo $repo --log --exit-status

while true; do
    status=$(gh run view $run_id --repo $repo --json status --jq '.status')
    if [ "$status" != "in_progress" ]; then
        echo "Workflow run $run_id has finished with status: $status"
        break
    fi
    sleep 10
done
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. If not provided, the latest run will be used.", required=False),
    ],
    long_running=True
)

# Register the stream_workflow_logs tool
tool_registry.register("github", stream_workflow_logs)
