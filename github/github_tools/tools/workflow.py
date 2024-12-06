from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# Essential log processing functions
LOG_PROCESSING_FUNCTIONS = '''
# Generic log processor with minimal buffer
function process_logs() {
    local pattern="$1"
    local max_lines="$2"
    
    awk -v pattern="$pattern" -v max_lines="$max_lines" '
        BEGIN {
            buffer_size = 10
            line_count = 0
        }
        
        {
            # Store in small circular buffer
            buffer[NR % buffer_size] = $0
            
            if (pattern && $0 ~ pattern) {
                # Show match with minimal context
                print "\\n---"
                for (i = 5; i > 0; i--) {
                    idx = ((NR - i) % buffer_size)
                    if (buffer[idx]) print buffer[idx]
                }
                print ">>> " $0 "\\n"
            }
            
            # Count lines for limit
            line_count++
            if (max_lines && line_count >= max_lines) exit
        }
    '
}
'''

# Core workflow tools
workflow_list = GitHubCliTool(
    name="github_workflow_list",
    description="List GitHub Actions workflows",
    content="gh workflow list --repo $repo $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="limit", type="int", description="Maximum workflows to list", required=False),
    ],
)

workflow_view = GitHubCliTool(
    name="github_workflow_view",
    description="View workflow details",
    content="gh workflow view --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

workflow_run = GitHubCliTool(
    name="github_workflow_run",
    description="Run a workflow",
    content="gh workflow run --repo $repo $workflow $([[ -n \"$ref\" ]] && echo \"--ref $ref\") $([[ -n \"$inputs\" ]] && echo \"--raw-field $inputs\")",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
        Arg(name="ref", type="str", description="Branch or tag name", required=False),
        Arg(name="inputs", type="str", description="JSON inputs {key:value}", required=False),
    ],
)

workflow_enable = GitHubCliTool(
    name="github_workflow_enable",
    description="Enable a workflow",
    content="gh workflow enable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

workflow_disable = GitHubCliTool(
    name="github_workflow_disable",
    description="Disable a workflow",
    content="gh workflow disable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

# Log viewing tools with efficient processing
workflow_logs = GitHubCliTool(
    name="github_workflow_logs",
    description="View workflow run logs with error context",
    content='''
#!/bin/sh
set -e

echo " Fetching logs for run ID: $run_id"

# Try to get logs with multiple methods
LOGS=""

# First try: Get failed logs
if [ -z "$LOGS" ]; then
    LOGS=$(gh run view --repo "$repo" "$run_id" --log-failed 2>/dev/null || true)
fi

# Second try: Get all logs
if [ -z "$LOGS" ]; then
    LOGS=$(gh run view --repo "$repo" "$run_id" --log 2>/dev/null || true)
fi

# Third try: Get raw logs via API
if [ -z "$LOGS" ]; then
    LOGS=$(gh api "repos/$repo/actions/runs/$run_id/logs" --raw 2>/dev/null || true)
fi

if [ -z "$LOGS" ]; then
    echo "❌ No logs available for run ID: $run_id"
    echo "Possible reasons:"
    echo "  • Run is still in progress"
    echo "  • Run has been deleted"
    echo "  • No permission to access logs"
    echo "  • Logs have expired"
    exit 1
fi

# Process and display logs
if [ -n "$search" ]; then
    echo "🔍 Filtering logs for: $search"
    echo "$LOGS" | grep -A 2 -B 2 "$search" || echo "No matches found"
else
    # Show logs with basic formatting
    echo "$LOGS" | while IFS= read -r line; do
        # Highlight errors and important messages
        if echo "$line" | grep -qi "error\\|failed\\|exception"; then
            echo "❌ $line"
        elif echo "$line" | grep -qi "warning"; then
            echo "⚠️  $line"
        elif echo "$line" | grep -qi "success\\|completed"; then
            echo "✅ $line"
        else
            echo "   $line"
        fi
    done
fi
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID", required=True),
        Arg(name="search", type="str", description="Optional: Search pattern", required=False),
    ],
)

workflow_run_list = GitHubCliTool(
    name="github_workflow_run_list",
    description="List workflow runs",
    content="gh run list --repo $repo $([[ -n \"$workflow\" ]] && echo \"--workflow $workflow\") $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Optional: Workflow name/ID", required=False),
        Arg(name="limit", type="int", description="Maximum runs to list", required=False),
    ],
)

workflow_run_view = GitHubCliTool(
    name="github_workflow_run_view",
    description="View workflow run details",
    content="gh run view --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to view", required=True),
    ],
)

workflow_run_cancel = GitHubCliTool(
    name="github_workflow_run_cancel",
    description="Cancel a workflow run",
    content="gh run cancel --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to cancel", required=True),
    ],
)

workflow_run_rerun = GitHubCliTool(
    name="github_workflow_run_rerun",
    description="Rerun a workflow",
    content="gh run rerun --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to rerun", required=True),
    ],
)

workflow_create = GitHubCliTool(
    name="github_workflow_create",
    description="Create a workflow",
    content="""
mkdir -p .github/workflows
echo "$content" > .github/workflows/$name
gh workflow enable --repo $repo .github/workflows/$name
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="name", type="str", description="Workflow filename", required=True),
        Arg(name="content", type="str", description="YAML workflow content", required=True),
    ],
)

workflow_delete = GitHubCliTool(
    name="github_workflow_delete",
    description="Delete a workflow",
    content="gh api --method DELETE /repos/$repo/actions/workflows/$workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow ID", required=True),
    ],
)

# Register all tools
WORKFLOW_TOOLS = [
    workflow_list, workflow_view, workflow_run, workflow_enable, workflow_disable,
    workflow_logs, workflow_run_list, workflow_run_view, workflow_run_cancel,
    workflow_run_rerun, workflow_create, workflow_delete
]

for tool in WORKFLOW_TOOLS:
    tool_registry.register("github", tool)