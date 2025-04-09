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
            # Configure sizes
            max_buffer = 100    # Lines to keep before error
            after_lines = 20    # Lines to show after error
            buffer_size = 0     # Current buffer size
            buffer_start = 0    # Start position in circular buffer
            printing = 0        # Number of lines left to print after match
            found_error = 0     # Track if we found any errors
            
            # Error patterns
            err_pattern = "(error|Error|ERROR|exited|Exited|failed|Failed|FAILED|exit code|Exception|EXCEPTION|fatal|Fatal|FATAL)"
            # Noise patterns to filter
            noise_pattern = "(Download|Progress|download|progress)"
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
            
            # Check for errors
            if ($0 ~ err_pattern) {
                found_error = 1
                # Generate a hash of the surrounding context to avoid duplicates
                context = ""
                for (i = 0; i < 3; i++) {  # Use 3 lines for context hash
                    pos = (buffer_pos - i + max_buffer) % max_buffer
                    if (buffer[pos]) {
                        context = context buffer[pos]
                    }
                }
                context_hash = context
                
                # Only print if we have not seen this context
                if (!(context_hash in seen)) {
                    seen[context_hash] = 1
                    
                    # Print separator for readability
                    print "\\n=== Error Context ===\\n"
                    
                    # Print buffer content (previous lines)
                    for (i = 0; i < buffer_size; i++) {
                        pos = (buffer_start + i) % max_buffer
                        print buffer[pos]
                    }
                    
                    # Start printing aftermath
                    printing = after_lines
                }
            }
            else if (printing > 0) {
                print
                printing--
                if (printing == 0) {
                    print "\\n=== End of Context ===\\n"
                }
            }
        }
        
        END {
            if (!found_error) {
                print "No error patterns found in the logs."
            }
        }
    '
}

# Function to search logs with context efficiently
function search_logs_with_context() {
    local pattern="$1"
    local before_context="${2:-5}"
    local after_context="${3:-5}"
    
    awk -v pattern="$pattern" -v before="$before_context" -v after="$after_context" '
        BEGIN {
            # Initialize circular buffer
            max_buffer = before + 1
            buffer_size = 0
            buffer_start = 0
            printing = 0
            found_match = 0
            
            # Noise pattern to filter
            noise_pattern = "(Download|Progress|download|progress)"
        }
        
        # Skip noisy lines early
        $0 ~ noise_pattern { next }
        
        {
            # Store in circular buffer
            buffer_pos = (buffer_start + buffer_size) % max_buffer
            buffer[buffer_pos] = $0
            
            if (buffer_size < max_buffer) {
                buffer_size++
            } else {
                buffer_start = (buffer_start + 1) % max_buffer
            }
            
            # Check for pattern match
            if ($0 ~ pattern) {
                found_match = 1
                # Generate context hash to avoid duplicates
                context_hash = $0  # Use matching line as hash
                
                if (!(context_hash in seen)) {
                    seen[context_hash] = 1
                    
                    print "\\n=== Match Found ===\\n"
                    
                    # Print previous lines from buffer
                    for (i = 0; i < buffer_size - 1; i++) {
                        pos = (buffer_start + i) % max_buffer
                        print "BEFORE | " buffer[pos]
                    }
                    
                    # Print matching line
                    print "MATCH  | " $0
                    
                    # Start printing aftermath
                    printing = after
                }
            }
            else if (printing > 0) {
                print "AFTER  | " $0
                printing--
                if (printing == 0) {
                    print "\\n=== End of Match ===\\n"
                }
            }
        }
        
        END {
            if (!found_match) {
                print "No matches found for pattern: " pattern
            }
        }
    '
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
    name="workflow_run_logs_failed",
    description="""View failed job outputs from GitHub Actions workflow run with advanced error detection.
    
Shows only the failed job logs with:
- Automatic error context extraction
- Smart filtering of noise
- Configurable context lines around errors
- Default shows last 100 lines if not searching""",
    content=f"""
#!/bin/sh
set -e

{LOG_PROCESSING_FUNCTIONS}

# Enforce maximum lines limit
MAX_LINES=150
LINES=${{tail_lines:-100}}

echo "🔍 Finding failed workflow runs in: $repo"

# Get recent failed runs
FAILED_RUNS=$(gh run list --repo "$repo" --json databaseId,name,conclusion,createdAt,url \
    --jq '[.[] | select(.conclusion == "failure")] | sort_by(.createdAt) | reverse | .[0:5]')

if [ -z "$FAILED_RUNS" ] || [ "$FAILED_RUNS" = "[]" ]; then
    echo "✅ No failed runs found in recent history"
    exit 0
fi

echo "📊 Fetching failed job logs for run ID: $run_id"

# First attempt - try getting failed logs directly
LOGS=$(gh run view --repo $repo $run_id --log-failed 2>/dev/null)
if [ -z "$LOGS" ]; then
    echo "⚠️ No failed logs found directly, attempting to get full logs..."
    # Second attempt - get full logs and filter for errors
    LOGS=$(gh run view --repo $repo $run_id --log 2>/dev/null)
fi

if [ -z "$LOGS" ]; then
    echo "❌ No logs available for this run. The run may still be in progress or logs have expired."
    exit 1
fi

if [ -n "$pattern" ]; then
    echo "🔍 Searching for pattern '$pattern' in logs..."
    echo "$LOGS" | search_logs_with_context "$pattern" "${{before_context:-2}}" "${{after_context:-2}}"
else
    echo "🔍 Extracting error context from logs..."
    echo "$LOGS" | extract_error_context | tail -n $LINES
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
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID", required=True),
        Arg(name="show_logs", type="bool", description="Show logs even if run didn't fail", required=False, default="false"),
    ],
)

# Register all tools
WORKFLOW_TOOLS = [
    workflow_list, workflow_view, workflow_run, workflow_logs,
    workflow_enable, workflow_disable, workflow_run_logs_failed
]

for tool in WORKFLOW_TOOLS:
    tool_registry.register("github", tool)
