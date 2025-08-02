# New file for analytics-focused tools
from kubiya_workflow_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_workflow_sdk.tools.registry import tool_registry

workflow_analytics = GitHubCliTool(
    name="github_workflow_analytics", 
    description="Get comprehensive workflow analytics",
    content="""
echo "📊 Analyzing workflow performance..."
echo "📈 Analysis period: ${days:-30} days"

# Get workflow runs with detailed information
RUNS=$(gh run list --repo "${repo}" \
    $([ -n "${workflow}" ] && echo "--workflow ${workflow}") \
    --json startedAt,conclusion,event,headBranch,name,status,createdAt,updatedAt \
    --created ">=${days:-30} days ago" \
    --limit "${limit:-1000}")

# Process and output analytics in requested format
if [ "${format}" = "json" ]; then
    echo "$RUNS" | jq '{
        summary: {
            total_runs: length,
            success_rate: ([.[] | select(.conclusion == "success")] | length) / length * 100,
            avg_duration_minutes: ([.[] | (if .startedAt and .updatedAt then 
                (fromdateiso8601(.updatedAt) - fromdateiso8601(.startedAt)) / 60 
                else 0 end)] | add / length),
            total_time_hours: ([.[] | (if .startedAt and .updatedAt then 
                (fromdateiso8601(.updatedAt) - fromdateiso8601(.startedAt)) / 3600
                else 0 end)] | add)
        },
        by_workflow: group_by(.name) | map({
            name: .[0].name,
            runs: length,
            success_rate: ([.[] | select(.conclusion == "success")] | length) / length * 100,
            avg_duration_minutes: ([.[] | (if .startedAt and .updatedAt then
                (fromdateiso8601(.updatedAt) - fromdateiso8601(.startedAt)) / 60
                else 0 end)] | add / length),
            status_breakdown: group_by(.status) | map({key: .[0].status, count: length})
        }),
        by_trigger: group_by(.event) | map({
            trigger: .[0].event,
            count: length,
            success_rate: ([.[] | select(.conclusion == "success")] | length) / length * 100
        }),
        by_branch: group_by(.headBranch) | map({
            branch: .[0].headBranch,
            runs: length,
            success_rate: ([.[] | select(.conclusion == "success")] | length) / length * 100
        })
    }'
else
    # Format as human-readable text
    echo "=== Workflow Analytics Summary ==="
    echo "$RUNS" | jq -r '
        "Total Runs: \(length)",
        "Success Rate: \(([.[] | select(.conclusion == "success")] | length) / length * 100 | round)%",
        "Average Duration: \(([.[] | (if .startedAt and .updatedAt then
            (fromdateiso8601(.updatedAt) - fromdateiso8601(.startedAt)) / 60
            else 0 end)] | add / length | round))m",
        "\nTop Workflows by Usage:",
        (group_by(.name) | sort_by(-length) | .[0:5] | map(
            "  • \(.[0].name): \(length) runs, \(([.[] | select(.conclusion == "success")] | length) / length * 100 | round)% success"
        ) | .[])'
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name/ID to analyze", required=False),
        Arg(name="days", type="str", description="Analysis period in days", required=False, default="30"),
        Arg(name="format", type="str", description="Output format (json/text)", required=False, default="text"),
        Arg(name="limit", type="str", description="Maximum runs to analyze", required=False, default="1000"),
    ],
)

security_scan = GitHubCliTool(
    name="github_security_scan",
    description="Scan repository for security issues and secrets",
    content="""
echo "🔒 Starting security scan..."
echo "📂 Repository: ${repo}"
echo "🔍 Scan type: ${scan_type:-'all'}"

# Create temporary directory for scanning
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository..."
if ! gh repo clone "${repo}" .; then
    echo "❌ Failed to clone repository"
    exit 1
fi

# Initialize results
FINDINGS=()

# Function to scan for secrets
scan_secrets() {
    echo "🔑 Scanning for exposed secrets..."
    
    # Common patterns for secrets
    PATTERNS=(
        "password[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "api[_]key[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "secret[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "aws[_]access[_]key[_]id[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "aws[_]secret[_]access[_]key[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "private[_]key[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"]"
        "[a-zA-Z0-9+/]{40,}"  # Base64 encoded strings
        "gh[ps]_[A-Za-z0-9_]{36,}"  # GitHub tokens
        "-----BEGIN.*PRIVATE KEY-----"
    )
    
    for pattern in "${PATTERNS[@]}"; do
        while IFS= read -r file; do
            if [ -f "$file" ] && [[ ! "$file" =~ ^\.git/ ]]; then
                matches=$(grep -Ein "$pattern" "$file" || true)
                if [ -n "$matches" ]; then
                    FINDINGS+=("⚠️  Potential secret in $file:\\n$matches")
                fi
            fi
        done < <(find . -type f)
    done
}

# Function to scan for security issues
scan_security() {
    echo "🛡️ Scanning for security issues..."
    
    # Check for vulnerable dependencies
    if [ -f "package.json" ]; then
        echo "📦 Checking npm dependencies..."
        if ! npm audit --json > npm_audit.json 2>/dev/null; then
            FINDINGS+=("⚠️  Vulnerable npm dependencies found")
        fi
    fi
    
    if [ -f "requirements.txt" ]; then
        echo "🐍 Checking Python dependencies..."
        if command -v safety >/dev/null; then
            safety check -r requirements.txt --json > python_audit.json 2>/dev/null || \
                FINDINGS+=("⚠️  Vulnerable Python dependencies found")
        fi
    fi
    
    # Check for common security misconfigurations
    if [ -f ".env" ]; then
        FINDINGS+=("⚠️  .env file found in repository")
    fi
    
    if [ -d ".git" ] && [ -f ".git/config" ]; then
        if grep -q "filemode = false" .git/config; then
            FINDINGS+=("⚠️  Git filemode is disabled, potential security risk")
        fi
    fi
}

# Perform requested scans
case "${scan_type}" in
    "secrets") scan_secrets ;;
    "security") scan_security ;;
    *) 
        scan_secrets
        scan_security
        ;;
esac

# Output findings
if [ ${#FINDINGS[@]} -eq 0 ]; then
    echo "✅ No security issues found"
else
    echo "🚨 Security issues found:"
    printf '%s\\n' "${FINDINGS[@]}"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="scan_type", type="str", description="Type of scan (all/secrets/security)", required=False, default="all"),
    ],
)

dependency_analytics = GitHubCliTool(
    name="github_dependency_analytics",
    description="Analyze repository dependencies and generate insights",
    content="""
echo "📦 Analyzing dependencies..."
echo "📂 Repository: ${repo}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo "📥 Cloning repository..."
if ! gh repo clone "${repo}" .; then
    echo "❌ Failed to clone repository"
    exit 1
fi

DEPS_INFO="{}"

# Analyze package.json if exists
if [ -f "package.json" ]; then
    echo "📊 Analyzing npm dependencies..."
    NPM_DEPS=$(jq '{
        dependencies: .dependencies,
        devDependencies: .devDependencies,
        total_deps: (.dependencies + .devDependencies | length)
    }' package.json)
    DEPS_INFO=$(echo "$DEPS_INFO" | jq '. + {npm: '$NPM_DEPS'}')
fi

# Analyze requirements.txt if exists
if [ -f "requirements.txt" ]; then
    echo "🐍 Analyzing Python dependencies..."
    PYTHON_DEPS=$(cat requirements.txt | grep -v "^#" | awk -F'==' '{print $1}' | jq -R -s -c 'split("\\n") | map(select(length > 0))')
    DEPS_INFO=$(echo "$DEPS_INFO" | jq '. + {python: {dependencies: '$PYTHON_DEPS', total_deps: ('$PYTHON_DEPS' | length)}}')
fi

# Analyze go.mod if exists
if [ -f "go.mod" ]; then
    echo "🔄 Analyzing Go dependencies..."
    GO_DEPS=$(awk '/^require[[:space:]]/ {p=1;next} /^)/ {p=0} p==1 {print $1}' go.mod | jq -R -s -c 'split("\\n") | map(select(length > 0))')
    DEPS_INFO=$(echo "$DEPS_INFO" | jq '. + {go: {dependencies: '$GO_DEPS', total_deps: ('$GO_DEPS' | length)}}')
fi

# Output analysis
if [ "${format}" = "json" ]; then
    echo "$DEPS_INFO"
else
    echo "=== Dependency Analysis ==="
    echo "$DEPS_INFO" | jq -r '
        if .npm then "NPM Dependencies: \(.npm.total_deps)" else empty end,
        if .python then "Python Dependencies: \(.python.total_deps)" else empty end,
        if .go then "Go Dependencies: \(.go.total_deps)" else empty end
    '
fi

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="format", type="str", description="Output format (json/text)", required=False, default="text"),
    ],
)

# Register all analytics tools
ANALYTICS_TOOLS = [
    workflow_analytics,
    security_scan,
    dependency_analytics,
]

for tool in ANALYTICS_TOOLS:
    tool_registry.register("github", tool)

__all__ = ['workflow_analytics', 'security_scan', 'dependency_analytics'] 