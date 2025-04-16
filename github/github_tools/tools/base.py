from kubiya_sdk.tools import Tool, FileSpec, Volume
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

# Function to add disclaimer
add_disclaimer() {{
    local format="$1"
    local message="$2"
    
    if [ "$format" = "markdown" ]; then
        echo "{KUBIYA_DISCLAIMER_MARKDOWN}" | envsubst
    else
        echo "{KUBIYA_DISCLAIMER_TEXT}" | envsubst
    fi
}}

{content}
'''

        # Generate operation-specific mermaid diagram
        mermaid_diagram = self._generate_mermaid_diagram(name, args)
            
        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image=GITHUB_CLI_DOCKER_IMAGE,
            content=enhanced_content,
            args=args,
            env=COMMON_ENV + [
                "KUBIYA_AGENT_PROFILE",
                "KUBIYA_AGENT_UUID",
            ],
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            with_volumes=with_volumes,
            mermaid=mermaid_diagram,
            with_files=with_files,
        )

    def _generate_mermaid_diagram(self, name, args):
        """Generate a GitHub operation-specific mermaid diagram."""
        diagram = ["graph TD"]
        
        if "workflow" in name:
            # Workflow-specific diagram
            diagram.extend([
                "    A[GitHub Actions] --> B{Check Workflow}",
                "    B -->|Exists| C[Get Workflow Details]",
                "    B -->|Not Found| D[Error: Invalid Workflow]",
                "    C --> E{Check Permissions}",
                "    E -->|Has Access| F[Execute Workflow Action]",
                "    E -->|No Access| G[Error: Permission Denied]",
                "    F --> H{Success?}",
                "    H -->|Yes| I[Return Results]",
                "    H -->|No| J[Handle Error]"
            ])
        elif "pr" in name:
            # PR-specific diagram
            diagram.extend([
                "    A[GitHub PR] --> B{Check Branch}",
                "    B -->|Valid| C[Get Branch Details]",
                "    B -->|Invalid| D[Error: Invalid Branch]",
                "    C --> E[Create/Update PR]",
                "    E --> F{PR Status}",
                "    F -->|Created| G[Add Reviewers]",
                "    F -->|Updated| H[Notify Updates]",
                "    G --> I[Return PR URL]",
                "    H --> I"
            ])
        elif "repo" in name:
            # Repository-specific diagram
            diagram.extend([
                "    A[GitHub Repo] --> B{Check Access}",
                "    B -->|Has Access| C[Get Repo Details]",
                "    B -->|No Access| D[Error: Permission Denied]",
                "    C --> E{Operation Type}",
                "    E -->|Read| F[Fetch Data]",
                "    E -->|Write| G[Modify Repo]",
                "    F --> H[Return Results]",
                "    G --> I{Changes Applied?}",
                "    I -->|Yes| J[Commit Changes]",
                "    I -->|No| K[Handle Error]"
            ])
        elif "file" in name:
            # File operation diagram
            diagram.extend([
                "    A[GitHub Files] --> B{Check Path}",
                "    B -->|Valid| C[Get File Content]",
                "    B -->|Invalid| D[Error: Invalid Path]",
                "    C --> E{Operation Type}",
                "    E -->|Read| F[Process Content]",
                "    E -->|Write| G[Modify Content]",
                "    F --> H[Return Results]",
                "    G --> I[Commit Changes]",
                "    I --> J[Create PR/Push]"
            ])
        else:
            # Generic GitHub operation diagram
            diagram.extend([
                "    A[GitHub API] --> B{Validate Input}",
                "    B -->|Valid| C[Execute Operation]",
                "    B -->|Invalid| D[Error: Invalid Input]",
                "    C --> E{Check Result}",
                "    E -->|Success| F[Return Data]",
                "    E -->|Failure| G[Handle Error]"
            ])

        return "\n".join(diagram)


class GitHubRepolessCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, with_volumes=None):
        if with_volumes is None:
            with_volumes = []
            
        enhanced_content = f"""
#!/bin/sh
set -e

echo "🔌 Connecting to GitHub..."

check_and_set_org() {{
    if [ -n "$org" ]; then
        echo "🏢 Using GitHub organization: $org"
    else
        orgs=$(gh api user/orgs --jq '.[].login')
        org_count=$(echo "$orgs" | wc -l)
        if [ "$org_count" -eq 0 ]; then
            echo "⚠️ Teammate environment authenticated GitHub user is not part of any organization."
        elif [ "$org_count" -eq 1 ]; then
            org=$orgs
            echo "🎯 Teammate environment authenticated GitHub user is part of one organization: $org. Using this organization."
        else
            echo "🏢 Teammate environment authenticated GitHub user is part of the following organizations:"
            echo "$orgs"
            echo "💡 Please specify the organization in your command if needed."
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
