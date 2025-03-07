#!/bin/bash
set -euo pipefail

# Constants for output limiting
MAX_EVENTS=25
MAX_PODS=50

# Function to handle cleanup
cleanup() {
    rm -f "${temp_files[@]}" 2>/dev/null
    kill $(jobs -p) 2>/dev/null || true
    exit "${1:-0}"
}
trap 'cleanup $?' EXIT INT TERM

# Array to track temporary files
declare -a temp_files
temp_dir=$(mktemp -d)
temp_files+=("$temp_dir")

# Function to create temp file
create_temp_file() {
    local tmp="${temp_dir}/$(uuidgen || date +%s.%N)"
    temp_files+=("$tmp")
    echo "$tmp"
}

# Function to format node status with emojis
format_node_status() {
    awk 'NR>1 {
        status=$2;
        emoji="❓";
        if (status == "Ready") emoji="✅";
        else if (status == "NotReady") emoji="❌";
        else if (status == "SchedulingDisabled") emoji="🚫";
        print "  " emoji " " $0;
    }'
}

echo "🏥 Cluster Health Summary"
echo "======================="

# Run checks in parallel
{
    # Node Status (background)
    {
        node_file=$(create_temp_file)
        echo "🖥️  Node Status:" > "$node_file"
        echo "-------------" >> "$node_file"
        kubectl $KUBECTL_AUTH_ARGS get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,ROLES:.metadata.labels.kubernetes\\.io/role,VERSION:.status.nodeInfo.kubeletVersion | format_node_status >> "$node_file" &
    }

    # Component Status (background)
    {
        component_file=$(create_temp_file)
        echo -e "\n🔧 Component Status:" > "$component_file"
        echo "----------------" >> "$component_file"
        kubectl $KUBECTL_AUTH_ARGS get componentstatuses -o custom-columns=NAME:.metadata.name,STATUS:.conditions[*].type,MESSAGE:.conditions[*].message | 
        awk 'NR>1 {
            status=$2;
            emoji="❓";
            if (status == "Healthy") emoji="✅";
            else if (status == "Unhealthy") emoji="❌";
            print "  " emoji " " $0;
        }' >> "$component_file" &
    }

    # Critical Pods Status (background)
    {
        pods_file=$(create_temp_file)
        echo -e "\n⚠️  Critical System Pods:" > "$pods_file"
        echo "--------------------" >> "$pods_file"
        kubectl $KUBECTL_AUTH_ARGS get pods -n kube-system --field-selector status.phase!=Running -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName |
        awk 'NR>1 {
            status=$2;
            emoji="❓";
            if (status == "Pending") emoji="⏳";
            else if (status == "Failed") emoji="❌";
            else if (status == "Unknown") emoji="❔";
            print "  " emoji " " $0;
        }' | head -n $MAX_PODS >> "$pods_file"
        pod_count=$(kubectl $KUBECTL_AUTH_ARGS get pods -n kube-system --field-selector status.phase!=Running --no-headers | wc -l)
        if [ "$pod_count" -gt "$MAX_PODS" ]; then
            echo "  ... and $(($pod_count - $MAX_PODS)) more" >> "$pods_file"
        fi &
    }

    # Recent Critical Events (background)
    {
        events_file=$(create_temp_file)
        echo -e "\n🚨 Recent Critical Events (last 30m):" > "$events_file"
        echo "--------------------------------" >> "$events_file"
        kubectl $KUBECTL_AUTH_ARGS get events --all-namespaces --sort-by=.metadata.creationTimestamp --field-selector type=Warning --since=30m |
        awk '{
            severity=$7;
            emoji="⚠️";
            if (severity ~ /Error/) emoji="❌";
            else if (severity ~ /Failed/) emoji="💔";
            else if (severity ~ /Killing/) emoji="💀";
            else if (severity ~ /BackOff/) emoji="🔄";
            print "  " emoji " " $0;
        }' | tail -n $MAX_EVENTS >> "$events_file"
        event_count=$(kubectl $KUBECTL_AUTH_ARGS get events --all-namespaces --field-selector type=Warning --since=30m --no-headers | wc -l)
        if [ "$event_count" -gt "$MAX_EVENTS" ]; then
            echo "  ... and $(($event_count - $MAX_EVENTS)) more events" >> "$events_file"
        fi &
    }

    # Resource Pressure (background)
    {
        pressure_file=$(create_temp_file)
        echo -e "\n📊 Resource Pressure:" > "$pressure_file"
        echo "-----------------" >> "$pressure_file"
        kubectl $KUBECTL_AUTH_ARGS get nodes -o json | 
        jq -r '.items[] | select(.status.conditions[] | select(.type | test("Pressure$"))) |
        "  \(.metadata.name):\n\(.status.conditions[] | select(.type | test("Pressure$")) |
        if .status == "True" then "    ❌ " else "    ✅ " end + .type + ": " + .message)"' >> "$pressure_file" &
    }

    # Wait for all background jobs to complete
    wait
} 2>/dev/null || true

# Output results in order
for file in "$node_file" "$component_file" "$pods_file" "$events_file" "$pressure_file"; do
    if [ -f "$file" ]; then
        cat "$file"
    fi
done