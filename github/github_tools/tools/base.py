from kubiya_sdk.tools.models import Tool, FileSpec
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"
GITHUB_CLI_DOCKER_IMAGE = "maniator/gh:latest"

KUBIYA_DISCLAIMER_MARKDOWN = '''

---
> 🤖 **Automated Action Notice**
> 
> This action was performed by [Kubiya.ai](https://kubiya.ai) teammate **${KUBIYA_AGENT_PROFILE}** on behalf of @${GITHUB_ACTOR}.
> 
> <details>
> <summary>Action Details</summary>
>
> - **Teammate ID**: [${KUBIYA_AGENT_UUID}](https://app.kubiya.ai/teammates/${KUBIYA_AGENT_UUID})
> - **Timestamp**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
> - **Operation**: ${OPERATION_TYPE}
> </details>
'''

KUBIYA_DISCLAIMER_TEXT = '''
---
🤖 Automated Action by Kubiya.ai
• Teammate: ${KUBIYA_AGENT_PROFILE}
• On behalf of: @${GITHUB_ACTOR}
• Teammate Configuration URL: https://app.kubiya.ai/teammates/${KUBIYA_AGENT_UUID}
• Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
'''

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, with_volumes=None, with_files=None):
        if with_volumes is None:
            with_volumes = []
        if with_files is None:
            with_files = []

        # Add disclaimer to content based on operation type
        enhanced_content = f'''
#!/bin/sh
set -e

# Set operation type for disclaimer
OPERATION_TYPE="{name}"

if ! command -v jq >/dev/null 2>&1; then
    apk add --quiet jq >/dev/null 2>&1
fi

if ! command -v python3 >/dev/null 2>&1; then
    apk add --quiet python3 py3-pip >/dev/null 2>&1
fi

pip3 install --quiet jinja2 >/dev/null 2>&1

{content}
'''
            
        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image=GITHUB_CLI_DOCKER_IMAGE,
            content=enhanced_content,
            with_files=with_files,
            args=args,
            env=COMMON_ENV + [
                "KUBIYA_AGENT_PROFILE",
                "KUBIYA_AGENT_UUID",
            ],
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            with_volumes=with_volumes
        )

    def register(self, namespace: str):
        """Register the tool with the given namespace."""
        tool_registry.register(namespace, self)
        return self

class GitHubRepolessCliTool(GitHubCliTool):
    def __init__(self, name, description, content, args=None, with_files=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            with_files=with_files or []
        )

# Define stream_workflow_logs tool
stream_workflow_logs = GitHubCliTool(
    name="github_stream_workflow_logs",
    description="Stream logs from a GitHub Actions workflow run in real-time. DO NOT USE THIS TOOL IF THE WORKFLOW IS ALREADY FAILED. (eg. received notification that the workflow failed)",
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