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

# Function to parse timestamp from log line
function parse_timestamp() {
    local line="$1"
    echo "$line" | grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}Z" || echo ""
}

# Function to determine log level
function get_log_level() {
    local line="$1"
    if echo "$line" | grep -qi "error\\|failed\\|exception"; then
        echo "ERROR"
    elif echo "$line" | grep -qi "warning\\|warn"; then
        echo "WARN"
    elif echo "$line" | grep -qi "info\\|notice"; then
        echo "INFO"
    elif echo "$line" | grep -qi "debug"; then
        echo "DEBUG"
    elif echo "$line" | grep -qi "success\\|completed"; then
        echo "SUCCESS"
    else
        echo "INFO"
    fi
}
'''

# Core workflow tools
workflow_list = GitHubCliTool(
    name="github_workflow_list",
    description="List GitHub Actions workflows",
    content="""
echo "📋 Fetching workflow list..."
echo "🔗 Workflows URL: https://github.com/$repo/actions"
echo "📊 Resource Overview:"
echo "  • Repository: $repo"
echo "  • Limit: ${limit:-'No limit'}"

if ! gh workflow list --repo $repo $([[ -n \"$limit\" ]] && echo \"--limit $limit\"); then
    echo "❌ Failed to list workflows. Common issues:"
    echo "  • Repository may not exist"
    echo "  • No workflows configured"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully retrieved workflow list!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="limit", type="int", description="Maximum workflows to list", required=False),
    ],
)

workflow_view = GitHubCliTool(
    name="github_workflow_view",
    description="View workflow details",
    content="""
echo "🔍 Fetching workflow details..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow: $workflow"
echo "  • URL: https://github.com/$repo/actions/workflows/$workflow"

if ! gh workflow view --repo $repo $workflow; then
    echo "❌ Failed to view workflow. Common issues:"
    echo "  • Workflow ID/name may be invalid"
    echo "  • Workflow may have been deleted"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully retrieved workflow details!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

workflow_run = GitHubCliTool(
    name="github_workflow_run",
    description="Run a workflow",
    content="""
echo "🚀 Triggering workflow..."
echo "📊 Run Configuration:"
echo "  • Repository: $repo"
echo "  • Workflow: $workflow"
echo "  • Branch/Ref: ${ref:-'default'}"
echo "  • Inputs: ${inputs:-'none'}"

if ! RESULT=$(gh workflow run --repo $repo $workflow $([[ -n "$ref" ]] && echo "--ref $ref") $([[ -n "$inputs" ]] && echo "--raw-field $inputs")); then
    echo "❌ Failed to trigger workflow. Common issues:"
    echo "  • Workflow may be disabled"
    echo "  • Invalid inputs provided"
    echo "  • Branch/ref may not exist"
    exit 1
fi

echo "✨ Workflow triggered successfully"
echo "📋 Details:"
echo "$RESULT"
""",
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
    content="""
echo "🔓 Enabling workflow..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow: $workflow"
echo "  • URL: https://github.com/$repo/actions/workflows/$workflow"

if ! gh workflow enable --repo $repo $workflow; then
    echo "❌ Failed to enable workflow. Common issues:"
    echo "  • Workflow may not exist"
    echo "  • Insufficient permissions"
    echo "  • Workflow already enabled"
    exit 1
fi
echo "✨ Workflow enabled successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

workflow_disable = GitHubCliTool(
    name="github_workflow_disable",
    description="Disable a workflow",
    content="""
echo "🔒 Disabling workflow..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow: $workflow"
echo "  • URL: https://github.com/$repo/actions/workflows/$workflow"

if ! gh workflow disable --repo $repo $workflow; then
    echo "❌ Failed to disable workflow. Common issues:"
    echo "  • Workflow may not exist"
    echo "  • Insufficient permissions"
    echo "  • Workflow already disabled"
    exit 1
fi
echo "✨ Workflow disabled successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

# Log viewing tools with efficient processing
workflow_logs = GitHubCliTool(
    name="github_workflow_logs",
    description="View workflow run logs with error context",
    content=f'''
#!/bin/sh
set -e
{LOG_PROCESSING_FUNCTIONS}

echo "🔍 Fetching logs for run ID: $run_id"
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Run ID: $run_id"
echo "  • URL: https://github.com/$repo/actions/runs/$run_id"

# Try to get logs with multiple methods
LOGS=""

# First try: Get failed logs
if [ -z "$LOGS" ]; then
    echo "->> Attempting to get failed logs..."
    LOGS=$(gh run view --repo "$repo" "$run_id" --log-failed 2>/dev/null || true)
fi

# Second try: Get all logs
if [ -z "$LOGS" ]; then
    echo "->> Attempting to get all logs..."
    LOGS=$(gh run view --repo "$repo" "$run_id" --log 2>/dev/null || true)
fi

# Third try: Get raw logs via API
if [ -z "$LOGS" ]; then
    echo "->> Failed to get logs via gh run view, trying API..."
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
    # Show logs with structured formatting
    echo "$LOGS" | while IFS= read -r line; do
        # Extract timestamp if present
        timestamp=$(parse_timestamp "$line")
        if [ -z "$timestamp" ]; then
            timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        fi
        
        # Determine log level and format line
        level=$(get_log_level "$line")
        case "$level" in
            "ERROR")   printf "[%s] %-7s ❌ %s\\n" "$timestamp" "$level" "$line" ;;
            "WARN")    printf "[%s] %-7s ⚠️  %s\\n" "$timestamp" "$level" "$line" ;;
            "SUCCESS") printf "[%s] %-7s ✅ %s\\n" "$timestamp" "$level" "$line" ;;
            "DEBUG")   printf "[%s] %-7s 🔍 %s\\n" "$timestamp" "$level" "$line" ;;
            *)        printf "[%s] %-7s ℹ️  %s\\n" "$timestamp" "$level" "$line" ;;
        esac
    done
fi
echo "✨ Log processing completed!"
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
    content="""
echo "📋 Fetching workflow runs..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow: ${workflow:-'All workflows'}"
echo "  • Limit: ${limit:-'No limit'}"
echo "  • URL: https://github.com/$repo/actions"

if [ -n "$workflow" ]; then
    echo "🔍 Filtering for workflow: $workflow"
fi

if ! gh run list --repo $repo \
    $([[ -n "$workflow" ]] && echo "--workflow $workflow") \
    $([[ -n "$limit" ]] && echo "--limit $limit") \
    --json status,databaseId,headBranch,event,title \
    --jq '.[] | "🔄 Run #\\(.databaseId) [\\(.status)] \\(.title) (\\(.event) on \\(.headBranch))"'; then
    echo "❌ Failed to list workflow runs. Common issues:"
    echo "  • Repository may not exist"
    echo "  • No workflow runs available"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully retrieved workflow runs!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Optional: Workflow name/ID", required=False),
        Arg(name="limit", type="int", description="Maximum runs to list", required=False),
    ],
)

workflow_run_view = GitHubCliTool(
    name="github_workflow_run_view",
    description="View workflow run details",
    content="""
echo "🔍 Fetching run details..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Run ID: $run_id"
echo "  • URL: https://github.com/$repo/actions/runs/$run_id"

if ! gh run view --repo $repo $run_id; then
    echo "❌ Failed to view run. Common issues:"
    echo "  • Run ID may be invalid"
    echo "  • Run may have been deleted"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully retrieved run details!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to view", required=True),
    ],
)

workflow_run_cancel = GitHubCliTool(
    name="github_workflow_run_cancel",
    description="Cancel a workflow run",
    content="""
echo "🛑 Canceling workflow run..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Run ID: $run_id"
echo "  • URL: https://github.com/$repo/actions/runs/$run_id"

if ! gh run cancel --repo $repo $run_id; then
    echo "❌ Failed to cancel run. Common issues:"
    echo "  • Run ID may be invalid"
    echo "  • Run may have already completed"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully canceled workflow run!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to cancel", required=True),
    ],
)

workflow_run_rerun = GitHubCliTool(
    name="github_workflow_run_rerun",
    description="Rerun a workflow",
    content="""
echo "🔄 Rerunning workflow..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Run ID: $run_id"
echo "  • URL: https://github.com/$repo/actions/runs/$run_id"

if ! gh run rerun --repo $repo $run_id; then
    echo "❌ Failed to rerun workflow. Common issues:"
    echo "  • Run ID may be invalid"
    echo "  • Run may not be rerunnable"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully triggered workflow rerun!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Run ID to rerun", required=True),
    ],
)

workflow_create = GitHubCliTool(
    name="github_workflow_create",
    description="Create a workflow",
    content="""
echo "📝 Creating new workflow..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow Name: $name"
echo "  • Path: .github/workflows/$name"

if ! mkdir -p .github/workflows; then
    echo "❌ Failed to create workflows directory"
    exit 1
fi

if ! echo "$content" > .github/workflows/$name; then
    echo "❌ Failed to write workflow file"
    exit 1
fi

if ! gh workflow enable --repo $repo .github/workflows/$name; then
    echo "❌ Failed to enable workflow. Common issues:"
    echo "  • Invalid YAML syntax"
    echo "  • Insufficient permissions"
    echo "  • Repository not found"
    exit 1
fi
echo "✨ Successfully created and enabled workflow!"
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
    content="""
echo "🗑️  Deleting workflow..."
echo "📊 Resource Details:"
echo "  • Repository: $repo"
echo "  • Workflow ID: $workflow"
echo "  • URL: https://github.com/$repo/actions/workflows/$workflow"

if ! gh api --method DELETE /repos/$repo/actions/workflows/$workflow; then
    echo "❌ Failed to delete workflow. Common issues:"
    echo "  • Workflow ID may be invalid"
    echo "  • Workflow may be in use"
    echo "  • Insufficient permissions"
    exit 1
fi
echo "✨ Successfully deleted workflow!"
""",
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