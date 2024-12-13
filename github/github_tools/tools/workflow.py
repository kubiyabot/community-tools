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

workflow_run_logs_failed = GitHubCliTool(
    name="github_workflow_run_logs_failed",
    description="Get logs from failed workflow runs with focus on error messages",
    content=f'''
#!/bin/sh
set -e
{LOG_PROCESSING_FUNCTIONS}

echo "🔍 Finding failed workflow runs in: $repo"

# Get recent failed runs
FAILED_RUNS=$(gh run list --repo "$repo" --json databaseId,name,conclusion,createdAt,url \
    --jq '[.[] | select(.conclusion == "failure")] | sort_by(.createdAt) | reverse | .[0:5]')

if [ -z "$FAILED_RUNS" ] || [ "$FAILED_RUNS" = "[]" ]; then
    echo "✅ No failed runs found in recent history"
    exit 0
fi

# Process each failed run
echo "$FAILED_RUNS" | jq -c '.[]' | while read -r run; do
    run_id=$(echo "$run" | jq -r '.databaseId')
    name=$(echo "$run" | jq -r '.name')
    date=$(echo "$run" | jq -r '.createdAt')
    url=$(echo "$run" | jq -r '.url')
    
    echo "\\n❌ Failed Run: $name"
    echo "📅 Date: $date"
    echo "🔗 URL: $url"
    echo "🆔 Run ID: $run_id"
    echo "\\n📝 Error Logs:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get logs and filter for errors/failures
    LOGS=$(gh run view --repo "$repo" "$run_id" --log || echo "No logs available")
    
    echo "$LOGS" | awk \'
        BEGIN {{ lines_printed = 0; context_lines = 3; buffer[""] = ""; buffer_size = 0; }}
        
        # Store line in circular buffer for context
        {{
            buffer[buffer_size % context_lines] = $0
            buffer_size++
        }}
        
        # Print error context when found
        /error|fail|exception|fatal/i {{
            if (lines_printed < 50) {{  # Limit total output
                print "\\n--- Error Context ---"
                # Print previous lines for context
                for (i = 1; i <= context_lines; i++) {{
                    idx = ((buffer_size - i - 1) + context_lines) % context_lines
                    if (buffer[idx] != "") print buffer[idx]
                }}
                print ">>> " $0  # Print the error line
                lines_printed += context_lines + 1
            }}
        }}
        
        END {{
            if (lines_printed == 0) print "No specific error messages found in logs"
        }}
    \'
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
done

echo "\\n✨ Log analysis complete!"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
    ],
)

workflow_run_logs_failed_by_id = GitHubCliTool(
    name="github_workflow_run_logs_failed_by_id",
    description="Get error logs from a specific failed workflow run",
    content=f'''
#!/bin/sh
set -e
{LOG_PROCESSING_FUNCTIONS}

echo "🔍 Checking workflow run #${{run_id}} in: ${{repo}}"

# Get run details
RUN_INFO=$(gh run view --repo "${{repo}}" "${{run_id}}" --json conclusion,name,createdAt,url,status || echo "{{}}") 

if [ "$RUN_INFO" = "{{}}" ]; then
    echo "❌ Run #${{run_id}} not found"
    exit 1
fi

CONCLUSION=$(echo "$RUN_INFO" | jq -r '.conclusion')
STATUS=$(echo "$RUN_INFO" | jq -r '.status')
NAME=$(echo "$RUN_INFO" | jq -r '.name')
DATE=$(echo "$RUN_INFO" | jq -r '.createdAt')
URL=$(echo "$RUN_INFO" | jq -r '.url')

echo "📋 Run Details:"
echo "━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔖 Name: $NAME"
echo "📅 Date: $DATE"
echo "📊 Status: $STATUS"
echo "🏁 Conclusion: $CONCLUSION"
echo "🔗 URL: $URL"

if [ "$CONCLUSION" != "failure" ]; then
    echo "\\n⚠️  This run did not fail (conclusion: $CONCLUSION)"
    if [ "${{show_logs}}" != "true" ]; then
        echo "Use --show-logs=true to see logs anyway"
        exit 0
    fi
fi

echo "\\n📝 Error Logs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━"

# Get logs and filter for errors/failures
LOGS=$(gh run view --repo "${{repo}}" "${{run_id}}" --log || echo "No logs available")

if [ "$LOGS" = "No logs available" ]; then
    echo "❌ No logs available for this run"
    exit 1
fi

echo "$LOGS" | awk \'
    BEGIN {{ 
        lines_printed = 0
        context_lines = 5  # Show more context for specific run
        buffer[""] = ""
        buffer_size = 0
        in_error_block = 0
        error_count = 0
    }}
    
    # Store line in circular buffer for context
    {{
        buffer[buffer_size % context_lines] = $0
        buffer_size++
    }}
    
    # Print error context when found
    /error|fail|exception|fatal|panic/i {{
        if (lines_printed < 100) {{  # Allow more lines for specific run
            if (!in_error_block) {{
                error_count++
                print "\\n🚫 Error Block #" error_count ":"
                print "-------------------"
                # Print previous lines for context
                for (i = 1; i <= context_lines; i++) {{
                    idx = ((buffer_size - i - 1) + context_lines) % context_lines
                    if (buffer[idx] != "") print "  " buffer[idx]
                }}
            }}
            print "❌ " $0
            in_error_block = 5  # Keep printing next 5 lines after error
            lines_printed++
        }}
    }}
    
    # Print following lines in error block
    {{
        if (in_error_block > 0 && lines_printed < 100) {{
            if (!/error|fail|exception|fatal|panic/i) {{
                print "  " $0
                lines_printed++
            }}
            in_error_block--
        }}
    }}
    
    END {{
        if (error_count == 0) {{
            print "No specific error messages found in logs"
        }} else {{
            print "\\nFound " error_count " error blocks"
            if (lines_printed >= 100) {{
                print "Output truncated. Use workflow_logs for full log"
            }}
        }}
    }}
\'
echo "━━━━━━━━━━━━━━━━━━━━━━━"
echo "\\n✨ Log analysis complete!"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID", required=True),
        Arg(name="show_logs", type="bool", description="Show logs even if run didn't fail", required=False, default="false"),
    ],
)

# Register all tools
WORKFLOW_TOOLS = [
    workflow_list, workflow_view, workflow_run, workflow_logs,
    workflow_enable, workflow_disable, workflow_run_logs_failed,
    workflow_run_logs_failed_by_id
]

for tool in WORKFLOW_TOOLS:
    tool_registry.register("github", tool)
