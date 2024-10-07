from kubiya_sdk.tools import Tool, FileSpec
from kubiya_sdk.tools import Arg
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"
GITHUB_CLI_DOCKER_IMAGE = "maniator/gh:latest"

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        enhanced_content = f"""
#!/bin/sh
set -e

if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Installing jq..."
    apk update && apk add --no-cache jq
fi

check_org() {{
    orgs=$(gh api user/orgs --jq '.[].login')
    if [ -z "$orgs" ]; then
        echo "You are not part of any organization."
    else
        echo "You are part of the following organizations:"
        echo "$orgs"
        echo "Please use one of these organizations in your command if needed."
    fi
}}

get_repo_context() {{
    if [ -z "$repo" ]; then
        echo "No repository specified. Here are your 10 most recently updated repositories:"
        gh repo list --limit 10 --json nameWithOwner --jq '.[].nameWithOwner'
        echo "NOTE: This is not a complete list of your repositories."
        echo "Please specify a repository in the format 'owner/repo' in your command."
        exit 1
    fi
}}

check_org
get_repo_context

{content}
"""

        updated_args = [arg for arg in args if arg.name not in ["org", "repo"]]
        updated_args.extend([
            Arg(name="org", type="str", description="GitHub organization name. Choose from the list of organizations displayed above.", required=False),
            Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. You can choose from the list of repositories displayed above, or specify another.", required=False)
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
            long_running=long_running
        )

# Add this new tool for streaming GitHub Actions workflow logs
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

# Don't forget to register the new tool
from kubiya_sdk.tools.registry import tool_registry
tool_registry.register("github", stream_workflow_logs)
