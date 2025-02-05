from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_finder_tool = KubernetesTool(
    name="resource_finder",
    description="Advanced Kubernetes resource finder with powerful search, analysis, and troubleshooting capabilities - use it to find resources in your cluster",
    content='''
    #!/bin/bash
    set -e

    # Constants for output
    MAX_MATCHES=50
    CONTEXT_LINES=2
    MAX_EVENTS=10

    # Function to normalize string for comparison
    normalize_string() {
        echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-._'
    }

    # Enhanced pattern matching function with multiple patterns support
    string_matches() {
        local str=$(normalize_string "$1")
        local patterns="$2"
        
        # Split patterns by comma and check each one
        IFS=',' read -ra PATTERNS <<< "$patterns"
        for p in "${PATTERNS[@]}"; do
            local pattern=$(normalize_string "$p")
            # Support for wildcard patterns
            if [[ "$pattern" == *"*"* ]]; then
                [[ "$str" == ${pattern} ]] && return 0
            # Support for exact matches with =
            elif [[ "$pattern" == "="* ]]; then
                [[ "$str" == "${pattern#=}" ]] && return 0
            # Support for negative matches with !
            elif [[ "$pattern" == "!"* ]]; then
                [[ "$str" != *"${pattern#!}"* ]] && return 0
            # Default partial match
            else
                [[ "$str" == *"$pattern"* ]] && return 0
            fi
        done
        return 1
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

    # Function to get all resource types
    get_resource_types() {
        local filter="$1"
        if [ -n "$filter" ]; then
            kubectl api-resources --no-headers | awk '{print $1}' | grep -i "$filter"
        else
            kubectl api-resources --no-headers | awk '{print $1}'
        fi
    }

    # Function to get resource aliases
    get_resource_aliases() {
        local resource="$1"
        kubectl api-resources --no-headers | awk -v res="$resource" '$1 == res || $2 == res {print $1, $2}' | tr ' ' '/'
    }

    # Enhanced search function with better pattern matching
    search_resources() {
        local patterns="$1"
        local namespace="$2"
        local kind="$3"
        local matches=0
        local total_matches=0
        
        # Build namespace flag
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"
        
        # Function to process a single resource
        process_resource() {
            local kind="$1"
            local name="$2"
            local ns="$3"
            local status="$4"
            local age="$5"
            local labels="$6"
            local annotations="$7"
            
            # Apply filters
            if [ -n "$status_filter" ] && ! status_matches "$status" "$status_filter"; then
                return
            fi
            
            if [ -n "$min_age" ]; then
                local age_seconds=$(get_age_seconds "$age")
                local min_age_seconds=$(get_age_seconds "$min_age")
                [ "$age_seconds" -lt "$min_age_seconds" ] && return
            fi
            
            if [ -n "$label_selector" ] && ! labels_match "$labels" "$label_selector"; then
                return
            fi
            
            # Check if any pattern matches name, labels, or annotations
            local matched=false
            if string_matches "$name" "$patterns" || \
               [ -n "$labels" ] && string_matches "$labels" "$patterns" || \
               [ -n "$annotations" ] && string_matches "$annotations" "$patterns"; then
                matched=true
            fi
            
            # If matched, show the resource
            if [ "$matched" = true ]; then
                # Show header for first match of this kind
                if [ "$matches" -eq 0 ]; then
                    echo -e "\n📦 $kind matches:"
                    echo "=================="
                fi
                
                format_resource "$kind" "$name" "$ns" "$status" "$age" "$labels"
                ((matches++))
                ((total_matches++))
                
                # Show health analysis if requested
                if [ "$analyze_health" = "true" ]; then
                    analyze_health "$kind" "$name" "$ns" "$status"
                fi
                
                # Show additional details if specified
                if [ "$show_details" = "true" ]; then
                    echo "  📋 Details:"
                    if [ "$show_yaml" = "true" ]; then
                        kubectl get "$kind" "$name" $ns_flag -o yaml | sed 's/^/    /'
                    else
                        kubectl describe "$kind" "$name" $ns_flag | sed 's/^/    /'
                    fi
                fi
                
                # Show recent events
                if [ "$show_events" = "true" ]; then
                    echo "  📅 Recent Events:"
                    kubectl get events $ns_flag --field-selector "involvedObject.name=$name,involvedObject.kind=$kind" \
                        --sort-by='.lastTimestamp' | tail -n $MAX_EVENTS | sed 's/^/    /'
                fi
                
                echo
            fi
        }
        
        # Process resources
        if [ -n "$kind" ]; then
            # Get aliases for the resource type
            local aliases=$(get_resource_aliases "$kind")
            if [ -z "$aliases" ]; then
                echo "⚠️  Warning: Resource type '$kind' not found"
                return
            fi
            
            matches=0
            kubectl get "$kind" $ns_flag --show-labels -o json | \
            jq -r '.items[] | [.metadata.namespace, .metadata.name, .status.phase // .status.conditions[-1].type // "Unknown", .metadata.creationTimestamp, .metadata.labels, .metadata.annotations] | @tsv' | \
            while IFS=$'\t' read -r ns name status timestamp labels annotations; do
                local age=$(get_relative_time "$timestamp")
                process_resource "$kind" "$name" "$ns" "$status" "$age" "$labels" "$annotations"
            done
        else
            # Get all resource types if none specified
            while read -r kind; do
                matches=0
                kubectl get "$kind" $ns_flag --show-labels -o json 2>/dev/null | \
                jq -r '.items[] | [.metadata.namespace, .metadata.name, .status.phase // .status.conditions[-1].type // "Unknown", .metadata.creationTimestamp, .metadata.labels, .metadata.annotations] | @tsv' | \
                while IFS=$'\t' read -r ns name status timestamp labels annotations; do
                    local age=$(get_relative_time "$timestamp")
                    process_resource "$kind" "$name" "$ns" "$status" "$age" "$labels" "$annotations"
                done
            done < <(get_resource_types "$resource_type_filter")
        fi
        
        return $total_matches
    }

    # Main execution
    {
        # Normalize and validate inputs
        pattern="${pattern:-}"
        namespace="${namespace:-}"
        resource_type="${resource_type:-}"
        resource_type_filter="${resource_type_filter:-}"
        show_details="${show_details:-false}"
        show_events="${show_events:-false}"
        show_labels="${show_labels:-false}"
        show_yaml="${show_yaml:-false}"
        analyze_health="${analyze_health:-false}"
        status_filter="${status_filter:-}"
        label_selector="${label_selector:-}"
        min_age="${min_age:-}"
        
        # If no pattern provided, show error
        if [ -z "$pattern" ]; then
            echo "❌ Error: Search pattern is required"
            exit 1
        fi
        
        echo "🔍 Searching for resources matching patterns: ${pattern}"
        [ -n "$namespace" ] && echo "📁 In namespace: ${namespace}"
        [ -n "$resource_type" ] && echo "📦 Resource type: ${resource_type}"
        [ -n "$resource_type_filter" ] && echo "🔍 Resource type filter: ${resource_type_filter}"
        [ -n "$status_filter" ] && echo "🎯 Status filter: ${status_filter}"
        [ -n "$label_selector" ] && echo "🏷️  Label selector: ${label_selector}"
        [ -n "$min_age" ] && echo "⏰ Minimum age: ${min_age}"
        echo "========================================"
        
        # Perform the search
        search_resources "$pattern" "$namespace" "$resource_type"
        matches=$?
        
        if [ "$matches" -eq 0 ]; then
            echo "❌ No resources found matching the criteria"
        else
            echo "✨ Found $matches matching resources"
        fi
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
            name="resource_type_filter",
            type="str",
            description="Filter by resource type (e.g., pod, deployment)",
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
            name="show_yaml",
            type="bool",
            description="Show resource as YAML instead of description",
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