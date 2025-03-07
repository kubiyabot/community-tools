#!/bin/bash
set -euo pipefail

# Constants for output limiting
MAX_PODS=50
MAX_COLUMNS_WIDTH=50

# Function to truncate long strings
truncate_string() {
    local str=$1
    local max_length=${2:-$MAX_COLUMNS_WIDTH}
    if [ ${#str} -gt "$max_length" ]; then
        echo "${str:0:$((max_length-3))}..."
    else
        echo "$str"
    fi
}

# Function to format pod status with emojis
format_pod_status() {
    awk -v max_width="$MAX_COLUMNS_WIDTH" '
    NR>1 {
        status=$3;
        emoji="❓";
        if (status == "Running") emoji="✅";
        else if (status == "Pending") emoji="⏳";
        else if (status == "Succeeded") emoji="🎉";
        else if (status == "Failed") emoji="❌";
        else if (status == "Unknown") emoji="❔";
        
        # Truncate name if too long
        name=$1;
        if (length(name) > max_width) {
            name = substr(name, 1, max_width-3) "...";
        }
        
        # Format output with fixed width columns
        printf "  %s %-'${MAX_COLUMNS_WIDTH}'s %-10s %-15s %s\n", emoji, name, status, $4, $6;
    }'
}

echo "📊 Pod Status Summary"
echo "==================="

# Set namespace flag and get total count
if [ -n "${namespace:-}" ]; then
    namespace_flag="--namespace $namespace"
    total_pods=$(kubectl $KUBECTL_AUTH_ARGS get pods $namespace_flag --no-headers | wc -l)
else
    namespace_flag="--all-namespaces"
    total_pods=$(kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces --no-headers | wc -l)
fi

# Get pod status with custom columns and formatting
kubectl $KUBECTL_AUTH_ARGS get pods $namespace_flag \
    -o custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace,STATUS:.status.phase,RESTARTS:.status.containerStatuses[*].restartCount,READY:.status.containerStatuses[*].ready,NODE:.spec.nodeName |
    format_pod_status | head -n $MAX_PODS

# Show summary if output was truncated
if [ "$total_pods" -gt "$MAX_PODS" ]; then
    echo -e "\n... and $(($total_pods - $MAX_PODS)) more pods"
fi

# Show status summary
echo -e "\n📈 Status Distribution:"
echo "-------------------"
if [ -n "${namespace:-}" ]; then
    kubectl $KUBECTL_AUTH_ARGS get pods $namespace_flag -o json |
    jq -r '.items | group_by(.status.phase) | map({"status": .[0].status.phase, "count": length}) | .[] |
    "\(.status): \(.count)"' |
    awk '{
        status=$1;
        count=$2;
        emoji="❓";
        if (status == "Running") emoji="✅";
        else if (status == "Pending") emoji="⏳";
        else if (status == "Succeeded") emoji="🎉";
        else if (status == "Failed") emoji="❌";
        else if (status == "Unknown") emoji="❔";
        printf "  %s %-10s: %d\n", emoji, status, count;
    }'
else
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o json |
    jq -r '.items | group_by(.status.phase) | map({"status": .[0].status.phase, "count": length}) | .[] |
    "\(.status): \(.count)"' |
    awk '{
        status=$1;
        count=$2;
        emoji="❓";
        if (status == "Running") emoji="✅";
        else if (status == "Pending") emoji="⏳";
        else if (status == "Succeeded") emoji="🎉";
        else if (status == "Failed") emoji="❌";
        else if (status == "Unknown") emoji="❔";
        printf "  %s %-10s: %d\n", emoji, status, count;
    }'
fi