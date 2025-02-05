from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_finder_tool = KubernetesTool(
    name="resource_finder",
    description="Find Kubernetes resources across your cluster with powerful search capabilities",
    content='''#!/bin/bash
set -e

# Function to normalize string for comparison
normalize_string() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-._'
}

# Function to check if labels match
labels_match() {
    local resource_labels="$1"
    local search_labels="$2"
    
    # Split search labels by comma and check each one
    IFS=',' read -ra LABEL_PAIRS <<< "$search_labels"
    for pair in "${LABEL_PAIRS[@]}"; do
        key=$(echo "$pair" | cut -d= -f1)
        value=$(echo "$pair" | cut -d= -f2)
        if ! echo "$resource_labels" | grep -q "$key=$value"; then
            return 1
        fi
    done
    return 0
}

# Function to format resource output
format_resource() {
    local kind="$1"
    local name="$2"
    local namespace="$3"
    local status="$4"
    local age="$5"
    local labels="$6"
    
    # Select emoji based on kind
    local emoji="📦"
    case "$kind" in
        Pod) emoji="🔵";;
        Deployment) emoji="🚀";;
        Service) emoji="🔌";;
        ConfigMap) emoji="⚙️";;
        Secret) emoji="🔒";;
        PersistentVolume) emoji="💾";;
        PersistentVolumeClaim) emoji="📂";;
        Namespace) emoji="📁";;
        Node) emoji="🖥️";;
        *) emoji="📦";;
    esac
    
    # Select status emoji
    local status_emoji="❓"
    case "$status" in
        *Running*|*Active*|*Bound*|*Ready*) status_emoji="✅";;
        *Pending*|*ContainerCreating*) status_emoji="⏳";;
        *Failed*|*Error*|*CrashLoopBackOff*) status_emoji="❌";;
        *Terminating*) status_emoji="🔄";;
        *NotReady*|*Unknown*) status_emoji="⚠️";;
        *) status_emoji="❓";;
    esac
    
    printf "%s %s/%s %s %s %s\\n" "$emoji" "${namespace:--}" "$name" "$kind" "$status_emoji" "$age"
}

# Main search function
search_resources() {
    local pattern="$1"
    local namespace="$2"
    local kind="$3"
    local label_selector="$4"
    local matches=0
    
    # Build namespace flag
    local ns_flag=""
    [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"
    
    # Build label selector flag
    local label_flag=""
    [ -n "$label_selector" ] && label_flag="-l $label_selector"
    
    # Function to process resources of a specific kind
    process_kind() {
        local kind="$1"
        echo -e "\n📦 $kind matches:"
        echo "=================="
        
        kubectl get "$kind" $ns_flag $label_flag -o json | \
        jq -r '.items[] | select(.metadata.name | ascii_downcase | contains($pattern | ascii_downcase)) | 
            [.metadata.namespace // "-", 
             .metadata.name, 
             .status.phase // .status.conditions[-1].type // "Unknown", 
             .metadata.creationTimestamp, 
             .metadata.labels] | @tsv' \
        --arg pattern "$pattern" | \
        while IFS=$'\t' read -r ns name status timestamp labels; do
            # Calculate age
            age=$(kubectl get "$kind" "$name" $ns_flag -o go-template='{{.metadata.creationTimestamp | ago}}' 2>/dev/null || echo "unknown")
            format_resource "$kind" "$name" "$ns" "$status" "$age" "$labels"
            ((matches++))
        done
    }
    
    # If specific kind is provided, search only that kind
    if [ -n "$kind" ]; then
        process_kind "$kind"
    else
        # Search common resource types
        for k in Pod Deployment Service ConfigMap Secret PersistentVolume PersistentVolumeClaim; do
            process_kind "$k"
        done
    fi
    
    if [ "$matches" -eq 0 ]; then
        echo "❌ No resources found matching the criteria"
    else
        echo -e "\n✨ Found $matches matching resources"
    fi
}

# Main execution
{
    pattern="{{.pattern}}"
    namespace="{{.namespace}}"
    kind="{{.resource_type}}"
    label_selector="{{.label_selector}}"
    
    # If no pattern provided, show error
    if [ -z "$pattern" ]; then
        echo "❌ Error: Search pattern is required"
        exit 1
    fi
    
    echo "🔍 Searching for resources matching: ${pattern}"
    [ -n "$namespace" ] && echo "📁 In namespace: ${namespace}"
    [ -n "$kind" ] && echo "📦 Resource type: ${kind}"
    [ -n "$label_selector" ] && echo "🏷️  Label selector: ${label_selector}"
    echo "========================================"
    
    # Perform the search
    search_resources "$pattern" "$namespace" "$kind" "$label_selector"
} | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
''',
    args=[
        Arg(
            name="pattern",
            type="str",
            description="Search pattern (case insensitive)",
            required=True
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace to search in (optional, searches all if not specified)",
            required=False
        ),
        Arg(
            name="resource_type",
            type="str",
            description="Specific resource type to search for (e.g., pod, deployment)",
            required=False
        ),
        Arg(
            name="label_selector",
            type="str",
            description="Filter by labels (e.g., 'app=nginx,env=prod')",
            required=False
        ),
    ],
)

# Register the tool
tool_registry.register("kubernetes", resource_finder_tool) 