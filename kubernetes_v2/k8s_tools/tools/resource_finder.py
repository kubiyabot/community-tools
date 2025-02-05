from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_finder_tool = KubernetesTool(
    name="resource_finder",
    description="Advanced Kubernetes resource finder with powerful search, analysis, and troubleshooting capabilities",
    content='''
    #!/bin/bash
    set -e

    # Constants for output
    MAX_MATCHES=50
    CONTEXT_LINES=2
    MAX_EVENTS=10

    # Function to normalize string for comparison
    normalize_string() {
        echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-.'
    }

    # Function to check if string matches pattern (case insensitive, partial match)
    string_matches() {
        local str=$(normalize_string "$1")
        local pattern=$(normalize_string "$2")
        [[ "$str" == *"$pattern"* ]]
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

    # Function to check if status matches filter
    status_matches() {
        local status="$1"
        local filter="$2"
        
        case "$filter" in
            healthy) [[ "$status" =~ Running|Active|Bound|Ready ]];;
            unhealthy) [[ "$status" =~ Failed|Error|CrashLoopBackOff|NotReady|Unknown ]];;
            pending) [[ "$status" =~ Pending|ContainerCreating|PodInitializing ]];;
            all) return 0;;
            *) [[ "$status" =~ $filter ]];;
        esac
    }

    # Function to get resource age in seconds
    get_age_seconds() {
        local age="$1"
        local value=$(echo "$age" | grep -o '[0-9]*')
        local unit=$(echo "$age" | grep -o '[a-zA-Z]*')
        
        case "$unit" in
            s) echo $value;;
            m) echo $((value * 60));;
            h) echo $((value * 3600));;
            d) echo $((value * 86400));;
            *) echo 0;;
        esac
    }

    # Function to analyze resource health
    analyze_health() {
        local kind="$1"
        local name="$2"
        local ns="$3"
        local status="$4"
        
        echo "  🔍 Health Analysis:"
        
        # Get resource-specific health info
        case "$kind" in
            Pod)
                # Check container statuses
                kubectl get pod "$name" -n "$ns" -o json | \
                jq -r '.status.containerStatuses[] | {
                    name: .name,
                    ready: .ready,
                    restartCount: .restartCount,
                    state: .state,
                    lastState: .lastState
                }' | \
                while read -r container; do
                    echo "    📦 Container: $(echo "$container" | jq -r .name)"
                    echo "      Ready: $(echo "$container" | jq -r .ready)"
                    echo "      Restarts: $(echo "$container" | jq -r .restartCount)"
                    echo "      State: $(echo "$container" | jq -r '.state | keys[0]')"
                done
                
                # Check resource usage
                echo "    💻 Resource Usage:"
                kubectl top pod "$name" -n "$ns" 2>/dev/null | tail -n 1 | \
                awk '{printf "      CPU: %s, Memory: %s\n", $2, $3}'
                ;;
                
            Deployment)
                # Check replica status
                kubectl get deployment "$name" -n "$ns" -o json | \
                jq -r '{
                    desired: .spec.replicas,
                    current: .status.replicas,
                    updated: .status.updatedReplicas,
                    available: .status.availableReplicas,
                    unavailable: .status.unavailableReplicas
                }' | \
                while read -r status; do
                    echo "    🔄 Replicas:"
                    echo "      Desired: $(echo "$status" | jq -r .desired)"
                    echo "      Current: $(echo "$status" | jq -r .current)"
                    echo "      Updated: $(echo "$status" | jq -r .updated)"
                    echo "      Available: $(echo "$status" | jq -r .available)"
                    echo "      Unavailable: $(echo "$status" | jq -r .unavailable)"
                done
                ;;
                
            Service)
                # Check endpoint status
                echo "    🔌 Endpoints:"
                kubectl get endpoints "$name" -n "$ns" -o json | \
                jq -r '.subsets[] | {
                    ready: (.addresses | length),
                    notReady: (.notReadyAddresses | length)
                }' | \
                while read -r status; do
                    echo "      Ready endpoints: $(echo "$status" | jq -r .ready)"
                    echo "      Not ready endpoints: $(echo "$status" | jq -r .notReady)"
                done
                ;;
        esac
        
        # Show recent warnings/errors
        echo "    ⚠️  Recent Issues:"
        kubectl get events -n "$ns" --field-selector "involvedObject.name=$name,involvedObject.kind=$kind,type!=Normal" \
            --sort-by='.lastTimestamp' | tail -n 3 | \
            awk '{printf "      %s: %s\n", $7, $8}'
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
        
        # Show labels if requested
        if [ "$show_labels" = "true" ] && [ -n "$labels" ]; then
            echo "  🏷️  Labels: $labels"
        fi
    }

    # Function to search resources with pattern
    search_resources() {
        local pattern="$1"
        local namespace="$2"
        local kind="$3"
        local matches=0
        
        # Build namespace flag
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"
        
        # Build kind flag
        local kind_flag=""
        [ -n "$kind" ] && kind_flag="$kind" || kind_flag="all"
        
        # Get resources with labels
        while IFS= read -r line; do
            if [[ $line =~ ^[[:space:]]*NAME ]]; then
                continue  # Skip header line
            fi
            
            # Parse the line
            if [ -n "$namespace" ]; then
                read -r name status age labels <<< "$line"
                ns="$namespace"
            else
                read -r ns name status age labels <<< "$line"
            fi
            
            # Skip if empty line
            [ -z "$name" ] && continue
            
            # Apply filters
            if [ -n "$status_filter" ] && ! status_matches "$status" "$status_filter"; then
                continue
            fi
            
            if [ -n "$min_age" ]; then
                local age_seconds=$(get_age_seconds "$age")
                local min_age_seconds=$(get_age_seconds "$min_age")
                [ "$age_seconds" -lt "$min_age_seconds" ] && continue
            fi
            
            if [ -n "$label_selector" ] && ! labels_match "$labels" "$label_selector"; then
                continue
            fi
            
            # Check if name matches pattern
            if string_matches "$name" "$pattern"; then
                format_resource "$kind" "$name" "$ns" "$status" "$age" "$labels"
                ((matches++))
                
                # Show health analysis if requested
                if [ "$analyze_health" = "true" ]; then
                    analyze_health "$kind" "$name" "$ns" "$status"
                fi
                
                # Show additional details if specified
                if [ "$show_details" = "true" ]; then
                    echo "  📋 Details:"
                    kubectl describe "$kind" "$name" $ns_flag | grep -A$CONTEXT_LINES -B$CONTEXT_LINES -i "$pattern" | sed 's/^/    /'
                fi
                
                # Show recent events
                if [ "$show_events" = "true" ]; then
                    echo "  📅 Recent Events:"
                    kubectl get events $ns_flag --field-selector "involvedObject.name=$name,involvedObject.kind=$kind" \
                        --sort-by='.lastTimestamp' | tail -n $MAX_EVENTS | sed 's/^/    /'
                fi
                
                echo
            fi
            
            # Check if we've reached max matches
            [ $matches -ge $MAX_MATCHES ] && {
                echo "⚠️  Reached maximum number of matches ($MAX_MATCHES). Use more specific search terms to see additional results."
                break
            }
        done < <(kubectl get "$kind_flag" $ns_flag --show-labels 2>/dev/null | tail -n +2)
    }

    # Main execution
    {
        # Normalize and validate inputs
        pattern="${pattern:-}"
        namespace="${namespace:-}"
        resource_type="${resource_type:-}"
        show_details="${show_details:-false}"
        show_events="${show_events:-false}"
        show_labels="${show_labels:-false}"
        analyze_health="${analyze_health:-false}"
        status_filter="${status_filter:-}"
        label_selector="${label_selector:-}"
        min_age="${min_age:-}"
        
        # If no pattern provided, show error
        if [ -z "$pattern" ]; then
            echo "❌ Error: Search pattern is required"
            exit 1
        fi
        
        # If resource type provided, validate it
        if [ -n "$resource_type" ]; then
            if ! kubectl api-resources --no-headers | awk '{print $1}' | grep -iq "^${resource_type}s\?$"; then
                echo "⚠️  Warning: Invalid resource type '${resource_type}'. Searching all resources instead."
                resource_type=""
            fi
        fi
        
        echo "🔍 Searching for resources matching '${pattern}'"
        [ -n "$namespace" ] && echo "📁 In namespace: ${namespace}"
        [ -n "$resource_type" ] && echo "📦 Resource type: ${resource_type}"
        [ -n "$status_filter" ] && echo "🎯 Status filter: ${status_filter}"
        [ -n "$label_selector" ] && echo "🏷️  Label selector: ${label_selector}"
        [ -n "$min_age" ] && echo "⏰ Minimum age: ${min_age}"
        echo "========================================"
        
        # If specific resource type provided, search only that
        if [ -n "$resource_type" ]; then
            search_resources "$pattern" "$namespace" "$resource_type"
        else
            # Search common resource types
            for kind in Pod Deployment Service ConfigMap Secret PersistentVolume PersistentVolumeClaim Namespace Node; do
                search_resources "$pattern" "$namespace" "$kind"
            done
        fi
        
        echo "✨ Search complete"
    } | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"
    ''',
    args=[
        Arg(
            name="pattern",
            type="str",
            description="Search pattern (case insensitive, partial match supported)",
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
            name="status_filter",
            type="str",
            description="Filter by status (healthy, unhealthy, pending, or custom regex)",
            required=False
        ),
        Arg(
            name="label_selector",
            type="str",
            description="Filter by labels (e.g., 'app=nginx,env=prod')",
            required=False
        ),
        Arg(
            name="min_age",
            type="str",
            description="Show only resources older than this (e.g., '1h', '2d')",
            required=False
        ),
        Arg(
            name="show_details",
            type="bool",
            description="Show additional details for matched resources",
            required=False
        ),
        Arg(
            name="show_events",
            type="bool",
            description="Show recent events for matched resources",
            required=False
        ),
        Arg(
            name="show_labels",
            type="bool",
            description="Show labels for matched resources",
            required=False
        ),
        Arg(
            name="analyze_health",
            type="bool",
            description="Perform health analysis on matched resources",
            required=False
        ),
    ],
)

# Register the tool
tool_registry.register("kubernetes", resource_finder_tool) 