from kubiya_sdk.tools.models import Tool, FileSpec
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"
GITHUB_CLI_DOCKER_IMAGE = "maniator/gh:latest"

# Shell script functions for log processing
LOG_PROCESSING_FUNCTIONS = """
function process_log {
    local log="\$1"
    echo "\$log" | while IFS= read -r line; do
        echo "\$line" | sed 's/\\x1b\\[[0-9;]*m//g'
    done
}

function format_timestamp {
    date -u "+%Y-%m-%d %H:%M:%S UTC"
}

function log_info {
    echo "ℹ️ \$(format_timestamp) - \$1"
}

function log_error {
    echo "❌ \$(format_timestamp) - \$1" >&2
}

function log_success {
    echo "✅ \$(format_timestamp) - \$1"
}

function stream_logs {
    local run_id="\$1"
    local repo="\$2"
    
    log_info "Starting log stream for run \$run_id"
    
    if ! gh run view "\$run_id" --repo "\$repo" --log 2>&1; then
        log_error "Failed to stream logs for run \$run_id"
        return 1
    fi
    
    local status
    status=\$(gh run view "\$run_id" --repo "\$repo" --json status --jq '.status' 2>/dev/null)
    
    case "\$status" in
        "completed")
            log_success "Workflow run completed"
            ;;
        "failure")
            log_error "Workflow run failed"
            return 1
            ;;
        *)
            log_info "Workflow status: \$status"
            ;;
    esac
}

function check_requirements {
    local missing_tools=()
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_tools+=("jq")
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        missing_tools+=("python3")
    fi
    
    if ! command -v envsubst >/dev/null 2>&1; then
        missing_tools+=("gettext")
    fi
    
    if [ \${#missing_tools[@]} -gt 0 ]; then
        log_info "Installing required tools: \${missing_tools[*]}"
        apk add --quiet \${missing_tools[@]} >/dev/null 2>&1
    fi
}
"""

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, with_volumes=None, with_files=None):
        if with_volumes is None:
            with_volumes = []
        if with_files is None:
            with_files = []

        # Add common shell functions and content
        enhanced_content = f"""#!/bin/bash
set -euo pipefail

{LOG_PROCESSING_FUNCTIONS}

# Check and install requirements
check_requirements

{content}
"""
            
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

# Update stream_workflow_logs tool
stream_workflow_logs = GitHubCliTool(
    name="github_stream_workflow_logs",
    description="Stream logs from a GitHub Actions workflow run in real-time.",
    content="""
if [ -z "\${run_id:-}" ]; then
    log_info "No run ID provided. Fetching the latest workflow run..."
    run_id=\$(gh run list --repo "\$repo" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null)
    if [ -z "\$run_id" ]; then
        log_error "No workflow runs found for the repository."
        exit 1
    fi
    log_info "Using the latest run ID: \$run_id"
fi

log_info "Streaming logs for workflow run \$run_id in repository \$repo..."
stream_logs "\$run_id" "\$repo"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. If not provided, the latest run will be used.", required=False),
    ],
    long_running=True
).register("github")