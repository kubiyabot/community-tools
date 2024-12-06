from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# First, let's add these shell functions at the beginning of the content for tools that need log processing
LOG_PROCESSING_FUNCTIONS = '''
# Function to extract relevant error context from logs efficiently
function extract_error_context() {
    awk '
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

workflow_list = GitHubCliTool(
    name="github_workflow_list",
    description="List GitHub Actions workflows in a repository.",
    content="gh workflow list --repo $repo $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="limit", type="int", description="Maximum number of workflows to list. Example: 10", required=False),
    ],
)

workflow_view = GitHubCliTool(
    name="github_workflow_view",
    description="View details of a specific GitHub Actions workflow.",
    content="gh workflow view --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_run = GitHubCliTool(
    name="github_workflow_run",
    description="Manually trigger a GitHub Actions workflow.",
    content="gh workflow run --repo $repo $workflow $([[ -n \"$ref\" ]] && echo \"--ref $ref\") $([[ -n \"$inputs\" ]] && echo \"--raw-field $inputs\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
        Arg(name="ref", type="str", description="Branch or tag name to run workflow on. Example: 'main'", required=False),
        Arg(name="inputs", type="str", description="JSON object of input keys and values. Example: '{\"name\":\"value\"}'", required=False),
    ],
)

workflow_disable = GitHubCliTool(
    name="github_workflow_disable",
    description="Disable a GitHub Actions workflow.",
    content="gh workflow disable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_enable = GitHubCliTool(
    name="github_workflow_enable",
    description="Enable a GitHub Actions workflow.",
    content="gh workflow enable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_create = GitHubCliTool(
    name="github_workflow_create",
    description="Create a new GitHub Actions workflow.",
    content="""
    mkdir -p .github/workflows
    echo "$content" > .github/workflows/$name
    gh workflow enable --repo $repo .github/workflows/$name
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="name", type="str", description="Name of the workflow file. Example: 'main.yml'", required=True),
        Arg(name="content", type="str", description="YAML content of the workflow. Example: 'name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v2\n      - run: npm test'", required=True),
    ],
)

workflow_delete = GitHubCliTool(
    name="github_workflow_delete",
    description="Delete a GitHub Actions workflow.",
    content="gh api --method DELETE /repos/$repo/actions/workflows/$workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow ID. Example: '1234567'", required=True),
    ],
)

workflow_run_list = GitHubCliTool(
    name="github_workflow_run_list",
    description="List recent runs of a GitHub Actions workflow.",
    content="gh run list --repo $repo --workflow $workflow $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
        Arg(name="limit", type="int", description="Maximum number of runs to list. Example: 10", required=False),
    ],
)

workflow_run_view = GitHubCliTool(
    name="github_workflow_run_view",
    description="View details of a specific workflow run.",
    content="gh run view --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_logs = GitHubCliTool(
    name="github_workflow_run_logs",
    description="""View GitHub Actions workflow logs with advanced search capabilities.
    
Shows workflow run logs (maximum 150 lines) with options to:
- Search for specific patterns with case sensitivity control
- Control context lines around matches (up to 5 lines before/after)
- Use exact match or regular expressions for searching
- Default shows last 100 lines if not searching""",
    content="""
# Enforce maximum lines limit
MAX_LINES=150
LINES=${tail_lines:-100}

if [ $LINES -gt $MAX_LINES ]; then
    LINES=$MAX_LINES
fi

if [ -n "$pattern" ]; then
    # Build grep options
    GREP_OPTS=""
    if [ "$case_sensitive" != "true" ]; then
        GREP_OPTS="$GREP_OPTS -i"  # Case insensitive by default
    fi
    if [ "$exact_match" = "true" ]; then
        GREP_OPTS="$GREP_OPTS -w"  # Word match
    fi
    
    # Set context lines (max 5 each)
    BEFORE_LINES=${before_context:-2}
    AFTER_LINES=${after_context:-2}
    if [ $BEFORE_LINES -gt 5 ]; then BEFORE_LINES=5; fi
    if [ $AFTER_LINES -gt 5 ]; then AFTER_LINES=5; fi
    
    echo "🔍 Searching for pattern '$pattern' in logs (📄 showing $BEFORE_LINES lines before and $AFTER_LINES lines after matches) 🎯"
    gh run view --repo $repo $run_id --log | tail -n $MAX_LINES | \
        grep $GREP_OPTS -B $BEFORE_LINES -A $AFTER_LINES "$pattern" | \
        head -n $LINES
else
    # Just show the last N lines
    echo "Showing last $LINES lines of logs"
    gh run view --repo $repo $run_id --log | tail -n $LINES
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
        Arg(name="tail_lines", type="int", description="Number of recent lines to show (1-150). Default: 100", required=False),
        Arg(name="pattern", type="str", description="Pattern to search in logs. Supports regular expressions", required=False),
        Arg(name="case_sensitive", type="bool", description="Make pattern matching case sensitive. Default: false", required=False),
        Arg(name="exact_match", type="bool", description="Match whole words only. Default: false", required=False),
        Arg(name="before_context", type="int", description="Lines to show before each match (max 5). Default: 2", required=False),
        Arg(name="after_context", type="int", description="Lines to show after each match (max 5). Default: 2", required=False),
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
    content="""
# Include the log processing functions
{LOG_PROCESSING_FUNCTIONS}

# Enforce maximum lines limit
MAX_LINES=150
LINES=${tail_lines:-100}

if [ $LINES -gt $MAX_LINES ]; then
    LINES=$MAX_LINES
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

# Create a temporary file for the logs
TEMP_LOG_FILE=$(mktemp)
echo "$LOGS" > "$TEMP_LOG_FILE"

if [ -n "$pattern" ]; then
    echo "🔍 Searching for pattern '$pattern' in logs..."
    RESULTS=$(cat "$TEMP_LOG_FILE" | search_logs_with_context "$pattern" "${before_context:-2}" "${after_context:-2}")
    if [ -n "$RESULTS" ]; then
        echo "$RESULTS"
    else
        echo "❌ No matches found for pattern: $pattern"
    fi
else
    echo "🔍 Extracting error context from logs..."
    RESULTS=$(cat "$TEMP_LOG_FILE" | extract_error_context)
    if [ -n "$RESULTS" ]; then
        echo "$RESULTS" | tail -n $LINES
    else
        echo "❌ No error patterns found in the logs"
        echo "Showing last $LINES lines of logs instead:"
        tail -n $LINES "$TEMP_LOG_FILE"
    fi
fi

# Clean up
rm -f "$TEMP_LOG_FILE"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
        Arg(name="tail_lines", type="int", description="Number of recent lines to show (1-150). Default: 100", required=False),
        Arg(name="pattern", type="str", description="Pattern to search in failed logs. Supports regular expressions", required=False),
        Arg(name="case_sensitive", type="bool", description="Make pattern matching case sensitive. Default: false", required=False),
        Arg(name="exact_match", type="bool", description="Match whole words only. Default: false", required=False),
        Arg(name="before_context", type="int", description="Lines to show before each match (max 5). Default: 2", required=False),
        Arg(name="after_context", type="int", description="Lines to show after each match (max 5). Default: 2", required=False),
    ],
)

workflow_run_cancel = GitHubCliTool(
    name="github_workflow_run_cancel",
    description="Cancel a workflow run.",
    content="gh run cancel --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_rerun = GitHubCliTool(
    name="github_workflow_run_rerun",
    description="Rerun a workflow run.",
    content="gh run rerun --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_clone_repo = GitHubCliTool(
    name="github_workflow_clone_repo",
    description="Clone a repository containing GitHub Actions workflows.",
    content="""
    echo "🔄 Cloning repository $repo into $([[ -n "$directory" ]] && echo "$directory" || echo "$(basename $repo)")"
    gh repo clone $repo $([[ -n "$directory" ]] && echo "$directory")
    cd $([[ -n "$directory" ]] && echo "$directory" || echo "$(basename $repo)")
    echo "Repository cloned successfully."
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="directory", type="str", description="Directory to clone into. If not specified, uses the repository name.", required=False),
    ],
)

workflow_discover_files = GitHubCliTool(
    name="github_workflow_discover_files",
    description="Discover GitHub Actions workflow files in a repository.",
    content="""
    echo "🔍 Discovering workflow files in repository $repo"
    gh repo clone $repo temp_repo
    cd temp_repo
    echo "Workflow files found:"
    find .github/workflows -name "*.yml" -o -name "*.yaml"
    cd ..
    rm -rf temp_repo
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

workflow_lint = GitHubCliTool(
    name="github_workflow_lint",
    description="Lint a GitHub Actions workflow file.",
    content="""
    echo "🔍 Linting workflow file $file_path"
    gh workflow lint $file_path
    """,
    args=[
        Arg(name="file_path", type="str", description="Path to the workflow file. Example: '.github/workflows/ci.yml'", required=True),
    ],
)

workflow_visualize = GitHubCliTool(
    name="github_workflow_visualize",
    description="Visualize a GitHub Actions workflow (outputs a URL to view the workflow).",
    content="""
    echo "🔍 Visualizing workflow $workflow_file in repository $repo"
    echo "https://github.com/$repo/actions/workflows/$(basename $workflow_file)"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow_file", type="str", description="Name of the workflow file. Example: 'ci.yml'", required=True),
    ],
)

workflow_dispatch_event = GitHubCliTool(
    name="github_workflow_dispatch_event",
    description="Manually trigger a workflow using the 'workflow_dispatch' event.",
    content="""
    echo "🔍 Triggering workflow $workflow_file in repository $repo"
    gh workflow run $workflow_file --repo $repo $([[ -n "$ref" ]] && echo "--ref $ref") $([[ -n "$inputs" ]] && echo "--raw-field $inputs")
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow_file", type="str", description="Name or ID of the workflow file. Example: 'ci.yml' or '1234567'", required=True),
        Arg(name="ref", type="str", description="The branch or tag name to run the workflow on. Example: 'main'", required=False),
        Arg(name="inputs", type="str", description="JSON object of input keys and values. Example: '{\"name\":\"value\"}'", required=False),
    ],
)

workflow_get_usage = GitHubCliTool(
    name="github_workflow_get_usage",
    description="Get the usage of GitHub Actions in a repository.",
    content="""
    gh api repos/$repo/actions/workflows | jq '.workflows[] | {name: .name, state: .state, path: .path}'
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

workflow_set_secret = GitHubCliTool(
    name="github_workflow_set_secret",
    description="Set a secret for GitHub Actions in a repository.",
    content="""
    echo "🔍 Setting secret $secret_name in repository $repo"
    gh secret set $secret_name --body "$secret_value" --repo $repo
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="secret_name", type="str", description="Name of the secret. Example: 'API_KEY'", required=True),
        Arg(name="secret_value", type="str", description="Value of the secret. Example: 'abcdef123456'", required=True),
    ],
)

# Register all workflow tools
for tool in [
    workflow_list, workflow_view, workflow_run, workflow_disable, workflow_enable,
    workflow_create, workflow_delete, workflow_run_list, workflow_run_view,
    workflow_run_logs, workflow_run_cancel, workflow_run_rerun,
    workflow_clone_repo, workflow_discover_files, workflow_lint,
    workflow_visualize, workflow_dispatch_event, workflow_get_usage,
    workflow_set_secret, workflow_run_logs_failed
]:
    tool_registry.register("github", tool)

__all__ = [
    'workflow_list', 'workflow_view', 'workflow_run', 'workflow_disable', 'workflow_enable',
    'workflow_create', 'workflow_delete', 'workflow_run_list', 'workflow_run_view',
    'workflow_run_logs', 'workflow_run_logs_failed', 'workflow_run_cancel', 'workflow_run_rerun',
    'workflow_clone_repo', 'workflow_discover_files', 'workflow_lint',
    'workflow_visualize', 'workflow_dispatch_event', 'workflow_get_usage',
    'workflow_set_secret'
]
