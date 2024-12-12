from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# Advanced log processing functions
LOG_PROCESSING_FUNCTIONS = '''
# Generic log processor with advanced functionality
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
                print "\\n--- Context Start ---\\n"
                for (i = 5; i > 0; i--) {
                    idx = ((NR - i) % buffer_size)
                    if (buffer[idx]) print buffer[idx]
                }
                print ">>> MATCH: " $0 "\\n--- Context End ---\\n"
            }
            
            # Count lines for limit
            line_count++
            if (max_lines && line_count >= max_lines) exit
        }
    '
}

# Function to extract timestamp from log line
function parse_timestamp() {
    local line="$1"
    echo "$line" | grep -o "[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}T[0-9]\\{2\\}:[0-9]\\{2\\}:[0-9]\\{2\\}Z" || echo ""
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

# GitHub CLI tools
workflow_list = GitHubCliTool(
    name="github_workflow_list",
    description="List GitHub Actions workflows",
    content="""
echo "📋 Fetching workflow list..."
gh workflow list --repo $repo --limit $([[ -n "$limit" ]] && echo "$limit") || exit 1
echo "✨ Successfully retrieved workflow list!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="limit", type="str", description="Maximum workflows to list", required=False),
    ],
)

workflow_view = GitHubCliTool(
    name="github_workflow_view",
    description="View workflow details",
    content="""
echo "🔍 Fetching workflow details..."
gh workflow view --repo $repo $workflow || exit 1
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
gh workflow run --repo $repo $workflow $([[ -n "$ref" ]] && echo "--ref $ref") $([[ -n "$inputs" ]] && echo "--inputs $inputs") || exit 1
echo "✨ Workflow triggered successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
        Arg(name="ref", type="str", description="Branch or tag name", required=False),
        Arg(name="inputs", type="str", description="JSON inputs {key:value}", required=False),
    ],
)

workflow_logs = GitHubCliTool(
    name="github_workflow_logs",
    description="View workflow run logs with advanced processing",
    content=f'''
#!/bin/sh
set -e
{LOG_PROCESSING_FUNCTIONS}

echo "🔍 Fetching logs for run ID: $run_id"
LOGS=$(gh run view --repo $repo $run_id --log || true)

if [ -z "$LOGS" ]; then
    echo "❌ No logs available for run ID: $run_id"
    exit 1
fi

if [ -n "$search" ]; then
    echo "🔍 Filtering logs for pattern: $search"
    echo "$LOGS" | process_logs "$search" 150
else
    echo "$LOGS" | while IFS= read -r line; do
        timestamp=$(parse_timestamp "$line")
        if [ -z "$timestamp" ]; then
            timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        fi
        
        level=$(get_log_level "$line")
        case "$level" in
            "ERROR")   printf "[%s] %-7s ❌ %s\\n" "$timestamp" "$level" "$line" ;;
            "WARN")    printf "[%s] %-7s ⚠️  %s\\n" "$timestamp" "$level" "$line" ;;
            "SUCCESS") printf "[%s] %-7s ✅ %s\\n" "$timestamp" "$level" "$line" ;;
            "DEBUG")   printf "[%s] %-7s 🔍 %s\\n" "$timestamp" "$level" "$line" ;;
            *)         printf "[%s] %-7s ℹ️  %s\\n" "$timestamp" "$level" "$line" ;;
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

workflow_enable = GitHubCliTool(
    name="github_workflow_enable",
    description="Enable a workflow",
    content="""
echo "🔓 Enabling workflow..."
gh workflow enable --repo $repo $workflow || exit 1
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
gh workflow disable --repo $repo $workflow || exit 1
echo "✨ Workflow disabled successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID", required=True),
    ],
)

# Register all tools
WORKFLOW_TOOLS = [
    workflow_list, workflow_view, workflow_run, workflow_logs,
    workflow_enable, workflow_disable
]

for tool in WORKFLOW_TOOLS:
    tool_registry.register("github", tool)
