# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

KUBERNETES_ICON_URL = "https://kubernetes.io/icons/icon-128x128.png"

# Default truncation settings
MAX_ITEMS = 50  # Maximum number of items to show in lists
MAX_OUTPUT_WIDTH = 120  # Maximum width for output lines
MAX_EVENTS = 25  # Maximum number of events to show
MAX_LOGS = 1000  # Maximum number of log lines

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Add truncation helper functions
        truncation_helpers = """
# Set global constants
set -euo pipefail
IFS=$'\\n\\t'

# Export constants with proper quoting
export MAX_ITEMS='50'
export MAX_OUTPUT_WIDTH='120'
export MAX_EVENTS='25'
export MAX_LOGS='1000'

# Truncation helper functions
truncate_output() {
    local max_items="${1:-$MAX_ITEMS}"
    local max_width="${2:-$MAX_OUTPUT_WIDTH}"
    
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
    }
    '
}

# Enhanced log handling function with improved error handling
get_logs_with_range() {
    local namespace="$1"
    local pod_name="$2"
    local container="${3:-}"
    local start_line="${4:-}"
    local end_line="${5:-}"
    local tail_lines="${6:-}"
    local since="${7:-}"
    local previous="${8:-}"
    
    # Validate required parameters
    if [[ -z "$namespace" || -z "$pod_name" ]]; then
        echo "❌ Error: namespace and pod_name are required" >&2
        return 1
    fi
    
    # Build base log command with proper quoting
    local log_cmd="kubectl logs \\"${pod_name}\\" -n \\"${namespace}\\""
    [[ -n "$container" ]] && log_cmd="$log_cmd -c \\"${container}\\""
    [[ -n "$since" ]] && log_cmd="$log_cmd --since=\\"${since}\\""
    [[ -n "$previous" ]] && log_cmd="$log_cmd --previous"
    
    # Verify pod exists before proceeding
    if ! kubectl get pod "$pod_name" -n "$namespace" >/dev/null 2>&1; then
        echo "❌ Error: Pod '$pod_name' not found in namespace '$namespace'" >&2
        return 1
    fi
    
    # If tail_lines is specified, it takes precedence over start/end lines
    if [[ -n "$tail_lines" ]]; then
        if ! [[ "$tail_lines" =~ ^[0-9]+$ ]]; then
            echo "❌ Error: tail_lines must be a positive integer" >&2
            return 1
        fi
        log_cmd="$log_cmd --tail=$tail_lines"
        eval "$log_cmd" | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
        return $?
    fi
    
    # If both start and end lines are specified, use sed to extract the range
    if [[ -n "$start_line" ]] && [[ -n "$end_line" ]]; then
        # Validate line numbers
        if ! [[ "$start_line" =~ ^[0-9]+$ ]] || ! [[ "$end_line" =~ ^[0-9]+$ ]]; then
            echo "❌ Error: start_line and end_line must be positive integers" >&2
            return 1
        fi
        
        if [[ "$start_line" -gt "$end_line" ]]; then
            echo "❌ Error: start_line ($start_line) cannot be greater than end_line ($end_line)" >&2
            return 1
        fi
        
        # Calculate range size
        local range_size=$((end_line - start_line + 1))
        
        # If range is larger than MAX_LOGS, warn and adjust
        if [[ "$range_size" -gt "$MAX_LOGS" ]]; then
            echo "⚠️  Warning: Requested range ($range_size lines) exceeds maximum allowed ($MAX_LOGS lines)" >&2
            echo "    Showing first $MAX_LOGS lines of the range" >&2
            end_line=$((start_line + MAX_LOGS - 1))
        fi
        
        eval "$log_cmd" | sed -n "${start_line},${end_line}p" | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
        return $?
    # If only start line is specified, show from that line to MAX_LOGS
    elif [[ -n "$start_line" ]]; then
        if ! [[ "$start_line" =~ ^[0-9]+$ ]]; then
            echo "❌ Error: start_line must be a positive integer" >&2
            return 1
        fi
        eval "$log_cmd" | tail -n "+$start_line" | head -n "$MAX_LOGS" | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
        return $?
    # If only end line is specified, show last N lines up to that line
    elif [[ -n "$end_line" ]]; then
        if ! [[ "$end_line" =~ ^[0-9]+$ ]]; then
            echo "❌ Error: end_line must be a positive integer" >&2
            return 1
        fi
        eval "$log_cmd" | head -n "$end_line" | tail -n "$MAX_LOGS" | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
        return $?
    # If no range specified, use default MAX_LOGS
    else
        eval "$log_cmd" | tail -n "$MAX_LOGS" | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
        return $?
    fi
}

# Wrapper for kubectl commands with truncation and improved error handling
kubectl_with_truncation() {
    local cmd="$1"
    local max_items="${2:-$MAX_ITEMS}"
    local max_width="${3:-$MAX_OUTPUT_WIDTH}"
    
    if [[ -z "$cmd" ]]; then
        echo "❌ Error: Command is required" >&2
        return 1
    fi
    
    # Validate numeric parameters
    if ! [[ "$max_items" =~ ^[0-9]+$ ]] || ! [[ "$max_width" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: max_items and max_width must be positive integers" >&2
        return 1
    fi
    
    eval "$cmd" | truncate_output "$max_items" "$max_width"
    return $?
}

# Helper function to format events with truncation and improved error handling
format_events() {
    local namespace="$1"
    local resource_name="$2"
    local resource_type="$3"
    
    # Validate required parameters
    if [[ -z "$namespace" || -z "$resource_name" || -z "$resource_type" ]]; then
        echo "❌ Error: namespace, resource_name, and resource_type are required" >&2
        return 1
    fi
    
    echo -e "\\n📜 Recent Events:"
    echo "==============="
    kubectl get events --namespace "$namespace" \
        --field-selector "involvedObject.name=$resource_name,involvedObject.kind=$resource_type" \
        --sort-by='.lastTimestamp' | \
    tail -n "$MAX_EVENTS" | \
    awk '
    BEGIN { OFS="  " }
    {
        emoji = "📝"
        if ($7 ~ /Warning/) emoji = "⚠️"
        else if ($7 ~ /Normal/) emoji = "ℹ️"
        print emoji, $0
    }' | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
    return $?
}

# Helper function to show resource status with truncation and improved error handling
show_resource_status() {
    local cmd="$1"
    local resource_type="$2"
    local name="$3"
    
    # Validate required parameters
    if [[ -z "$cmd" || -z "$resource_type" || -z "$name" ]]; then
        echo "❌ Error: cmd, resource_type, and name are required" >&2
        return 1
    fi
    
    echo -e "\\n📊 $resource_type Status:"
    echo "===================="
    if ! kubectl_with_truncation "$cmd" "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"; then
        echo "❌ Failed to get $resource_type status" >&2
        return 1
    fi
    return 0
}
"""

        inject_kubernetes_context = """
# Enable strict error handling
set -euo pipefail
IFS=$'\\n\\t'

# Define locations with proper quoting
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"

# Verify required files exist and are readable
if [[ ! -f "$TOKEN_LOCATION" ]]; then
    echo "❌ Error: Kubernetes token file not found at $TOKEN_LOCATION" >&2
    exit 1
fi

if [[ ! -f "$CERT_LOCATION" ]]; then
    echo "❌ Error: Kubernetes certificate file not found at $CERT_LOCATION" >&2
    exit 1
fi

if [[ ! -r "$TOKEN_LOCATION" ]]; then
    echo "❌ Error: Kubernetes token file is not readable at $TOKEN_LOCATION" >&2
    exit 1
fi

if [[ ! -r "$CERT_LOCATION" ]]; then
    echo "❌ Error: Kubernetes certificate file is not readable at $CERT_LOCATION" >&2
    exit 1
fi

# Read token securely
KUBE_TOKEN="$(cat "$TOKEN_LOCATION")"
if [[ -z "$KUBE_TOKEN" ]]; then
    echo "❌ Error: Kubernetes token file is empty" >&2
    exit 1
fi

# Configure kubectl with proper error handling
echo "🔧 Configuring Kubernetes context..."

if ! kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                       --certificate-authority="$CERT_LOCATION" >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes cluster configuration" >&2
    exit 1
fi

if ! kubectl config set-credentials in-cluster --token="$KUBE_TOKEN" >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes credentials" >&2
    exit 1
fi

if ! kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes context" >&2
    exit 1
fi

if ! kubectl config use-context in-cluster >/dev/null 2>&1; then
    echo "❌ Error: Failed to switch to in-cluster context" >&2
    exit 1
fi

# Verify connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Error: Failed to verify Kubernetes cluster connection" >&2
    exit 1
fi

echo "✅ Successfully configured Kubernetes context"
"""
        full_content = f"{inject_kubernetes_context}\n{truncation_helpers}\n{content}"

        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
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
