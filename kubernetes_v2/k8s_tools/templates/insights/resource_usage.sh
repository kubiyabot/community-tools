#!/bin/bash
set -euo pipefail

# Constants for output limiting
MAX_ITEMS=50
MAX_COLUMNS_WIDTH=30

# Function to handle cleanup
cleanup() {
    rm -f "${temp_files[@]}" 2>/dev/null
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

# Function to format resource usage with colors and limits
format_resource_usage() {
    awk -v max_width="$MAX_COLUMNS_WIDTH" '
    BEGIN {
        # Define color codes
        red="\033[31m";
        yellow="\033[33m";
        green="\033[32m";
        reset="\033[0m";
    }
    NR>1 {
        # Calculate CPU percentage
        cpu=$2
        gsub(/%/, "", cpu)
        cpu_num=cpu+0

        # Calculate memory percentage
        mem=$4
        gsub(/%/, "", mem)
        mem_num=mem+0

        # Determine colors based on usage
        cpu_color=green
        if (cpu_num >= 80) cpu_color=red
        else if (cpu_num >= 50) cpu_color=yellow

        mem_color=green
        if (mem_num >= 80) mem_color=red
        else if (mem_num >= 50) mem_color=yellow

        # Truncate name if too long
        name=$1
        if (length(name) > max_width) {
            name = substr(name, 1, max_width-3) "..."
        }

        # Format output with colors
        printf "  %-'${MAX_COLUMNS_WIDTH}'s %s%-6s%s %s %s%-6s%s %s\n", 
            name,
            cpu_color, $2, reset,
            $3,
            mem_color, $4, reset,
            $5
    }'
}

# Function to sort by resource usage
sort_by_usage() {
    local sort_field=$1
    local temp_file=$(create_temp_file)
    cat > "$temp_file"
    
    if [ "$sort_field" = "cpu" ]; then
        sort -k2 -rh "$temp_file"  # Sort by CPU (2nd field)
    else
        sort -k4 -rh "$temp_file"  # Sort by Memory (4th field)
    fi
}

echo "📊 Resource Usage Summary (showing top $MAX_ITEMS)"
echo "==========================================="

# Process nodes
echo "🖥️  Node Resource Usage:"
echo "-------------------"
echo "NAME                     CPU(cores)   CPU%     MEMORY(bytes)   MEMORY%"
kubectl $KUBECTL_AUTH_ARGS top nodes | sort_by_usage cpu | head -n $MAX_ITEMS | format_resource_usage

# Process pods
echo -e "\n🛠️  Pod Resource Usage:"
echo "-------------------"
echo "NAME                     CPU(cores)   CPU%     MEMORY(bytes)   MEMORY%   NAMESPACE"
if [ -n "${namespace:-}" ]; then
    kubectl $KUBECTL_AUTH_ARGS top pods --namespace "$namespace" --sort-by=cpu | head -n $MAX_ITEMS | format_resource_usage
else
    # Get all pods but process efficiently
    kubectl $KUBECTL_AUTH_ARGS top pods --all-namespaces --sort-by=cpu | head -n $MAX_ITEMS | format_resource_usage
fi

# Show resource summary
echo -e "\n📈 Resource Summary:"
echo "------------------"
# Get cluster-wide resource allocation
kubectl $KUBECTL_AUTH_ARGS describe nodes | grep -A 3 "Allocated resources:" | tail -n 3 |
awk '{
    if ($1 == "cpu") printf "CPU Usage:     %s/%s (%s)\n", $2, $4, $6;
    if ($1 == "memory") printf "Memory Usage:  %s/%s (%s)\n", $2, $4, $6;
}'