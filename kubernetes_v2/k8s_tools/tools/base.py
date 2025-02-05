# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

KUBERNETES_ICON_URL = "https://kubernetes.io/icons/icon-128x128.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Basic helper functions that don't interfere with the main script
        helpers = """
#!/bin/sh

# Set shell options for safety
set -e  # Exit on error
set -u  # Error on undefined variables

# Switch to bash if available (for advanced features)
if command -v bash >/dev/null 2>&1; then
    if [ -z "${BASH_VERSION:-}" ]; then
        exec bash "$0" "$@"
    fi
    # Enable bash-specific options
    set -o pipefail
    shopt -s nullglob >/dev/null 2>&1 || true
fi

# Set up temp directory first, before anything else runs
export TMPDIR="/dev/shm"

# Set default values for common variables
MAX_ITEMS=50
MAX_WIDTH=120
MAX_EVENTS=25
MAX_OUTPUT_LINES=50

# Initialize common optional parameters with defaults
grep_filter=${grep_filter:-}
container=${container:-}
namespace=${namespace:-default}
label=${label:-}
selector=${selector:-}
tail=${tail:-}
since=${since:-}
previous=${previous:-}
follow=${follow:-}

# Function to generate a unique ID without relying on uuidgen
generate_uuid() {
    echo "$(date +%s)-$(od -N 4 -t x4 /dev/urandom | head -1 | awk '{print $2}')"
}

# Alias uuidgen to our generate_uuid function for compatibility
uuidgen() {
    generate_uuid
}

# Helper functions
truncate_output() {
    local max_items=${1:-$MAX_ITEMS}
    local max_width=${2:-$MAX_WIDTH}
    awk -v max_items="$max_items" -v max_width="$max_width" '
    NR <= max_items {
        if (length($0) > max_width) {
            print substr($0, 1, max_width-3) "..."
        } else {
            print
        }
    }
    NR == max_items+1 {
        print "... output truncated ..."
    }'
}

# Helper function to format log lines safely
format_logs() {
    local input_file="$1"
    local max_lines="${2:-$MAX_OUTPUT_LINES}"
    local show_time="${3:-false}"
    
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file not found" >&2
        return 1
    fi
    
    # Count total lines
    local total_lines
    total_lines=$(wc -l < "$input_file")
    
    # Show header with total line count
    if [ "$total_lines" -gt "$max_lines" ]; then
        echo "Showing last $max_lines of $total_lines lines"
        echo "----------------------------------------"
    fi
    
    # Process the logs
    if [ "$show_time" = "true" ]; then
        # Show timestamps
        tail -n "$max_lines" "$input_file" | while IFS= read -r line; do
            printf "[%s] %s\\n" "$(date +%H:%M:%S)" "$line"
        done
    else
        # Show logs without timestamps
        tail -n "$max_lines" "$input_file"
    fi
}

# Helper function to safely get parameter values with defaults
get_param() {
    local param_name="$1"
    local default_value="${2:-}"
    
    # Use bash parameter expansion for safer variable handling
    local value
    value=${!param_name:-$default_value}
    echo "$value"
}

# Helper function to safely parse JSON using jq with null handling
parse_json() {
    local json="$1"
    local query="${2:-.}"  # Default to returning entire JSON if no query specified
    local default_value="${3:-}"  # Optional default value if result is null/missing
    
    if [ -z "$json" ]; then
        if [ -n "$default_value" ]; then
            echo "$default_value"
        else
            echo "{}"
        fi
        return
    fi
    
    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo "Warning: jq not available, returning raw JSON" >&2
        echo "$json"
        return
    fi
    
    # First validate if input is valid JSON
    if ! echo "$json" | jq '.' >/dev/null 2>&1; then
        echo "Warning: Invalid JSON input" >&2
        if [ -n "$default_value" ]; then
            echo "$default_value"
        else
            echo "{}"
        fi
        return
    fi
    
    # Try to parse with jq, handling null values
    local jq_script="
        # Helper to safely traverse paths
        def get_path(p):
            . as \$root |
            try
                reduce (p | split(\".\")) as \$key (
                    \$root;
                    if \$key == \"\" then .
                    elif . == null then null
                    else .[\$key] // null
                    end
                )
            catch
                null
            end;

        # Main query with safe traversal
        if \"$query\" == \".\" then
            .
        else
            get_path(\"$query\")
        end
    "
    
    local result
    result=$(echo "$json" | jq -r "$jq_script" 2>/dev/null)
    local jq_exit=$?
    
    if [ $jq_exit -ne 0 ] || [ "$result" = "null" ] || [ -z "$result" ]; then
        if [ -n "$default_value" ]; then
            echo "$default_value"
        else
            echo "{}"
        fi
    else
        echo "$result"
    fi
}

# Helper function to check if a pod exists
check_pod_exists() {
    local namespace="$1"
    local pod_name="$2"
    
    if [ -z "$namespace" ] || [ -z "$pod_name" ]; then
        echo "❌ Namespace and pod name are required" >&2
        return 1
    fi
    
    if ! kubectl get pod -n "$namespace" "$pod_name" >/dev/null 2>&1; then
        echo "❌ Pod '$pod_name' not found in namespace '$namespace'" >&2
        return 1
    fi
    
    return 0
}

# Helper function to wait for pod to be ready
wait_for_pod() {
    local namespace="$1"
    local pod_name="$2"
    local timeout="${3:-300}"  # Default 5 minutes timeout
    
    echo "⏳ Waiting for pod $pod_name to be ready (timeout: ${timeout}s)..."
    
    if ! kubectl wait --for=condition=ready pod -n "$namespace" "$pod_name" --timeout="${timeout}s" >/dev/null 2>&1; then
        echo "❌ Timeout waiting for pod $pod_name to be ready" >&2
        return 1
    fi
    
    echo "✅ Pod $pod_name is ready"
    return 0
}

# Helper function to get pod status with default value
get_pod_status() {
    local namespace="$1"
    local pod_name="$2"
    local default_status="${3:-Unknown}"
    
    if ! check_pod_exists "$namespace" "$pod_name"; then
        echo "$default_status"
        return 1
    fi
    
    local status
    status=$(kubectl get pod -n "$namespace" "$pod_name" -o json | parse_json '.status.phase' "$default_status")
    echo "$status"
}

# Setup working directories
setup_dirs() {
    # Create a unique working directory in our TMPDIR
    WORK_DIR="$TMPDIR/kubectl-$(generate_uuid)"
    mkdir -p "$WORK_DIR"
    echo "$WORK_DIR"
}
"""

        # Simple and robust context injection without chmod
        inject_kubernetes_context = """
set -eu

# Setup working directories and get the work dir path
WORK_DIR=$(setup_dirs)

# Use service account files directly from their original location
TOKEN_LOCATION="/var/run/secrets/kubernetes.io/serviceaccount/token"
CERT_LOCATION="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

# Set KUBECONFIG to a writable location
export KUBECONFIG="$WORK_DIR/config"

# Inject in-cluster context using the service account token directly
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                          --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "Error: Kubernetes service account token or cert not found at $TOKEN_LOCATION or $CERT_LOCATION"
    exit 1
fi

# Cleanup function
cleanup() {
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT
"""
        # Combine helpers and the actual content
        full_content = f"{helpers}\n{inject_kubernetes_context}\n{content}"

        # Mount service account files directly to their expected locations
        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/var/run/secrets/kubernetes.io/serviceaccount/token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            with_files=file_specs,
        )

# Example usage:
kubectl_cli = KubernetesTool(
    name="kubectl_cli",
    description="Runs any Kubernetes commands using the `kubectl` binary.",
    content="kubectl {{.command}}",
    args=[
        Arg(
            name="command",
            description="The Kubernetes CLI command to run. Do not use `kubectl`, only enter its command.",
            required=True
        )
    ]
)
