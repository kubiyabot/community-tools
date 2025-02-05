from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Common constants
MAX_OUTPUT_LINES = 100
MAX_EVENTS = 25
MAX_PODS = 50

node_management_tool = KubernetesTool(
    name="node_management",
    description="Manages and provides information about Kubernetes nodes",
    content='''
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)

    # Function to show resource status with limits
    show_resource_status() {
        local cmd="$1"
        local resource_type="$2"
        local resource_name="$3"
        
        if ! eval "$cmd" > "$temp_file"; then
            echo "❌ Failed to get $resource_type status"
            rm "$temp_file"
            exit 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering output with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return
            fi
            echo "$filtered_output" > "$temp_file"
        fi
        
        # Show limited output
        head -n $MAX_OUTPUT_LINES "$temp_file"
        
        # Show truncation message if needed
        total_lines=$(wc -l < "$temp_file")
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines lines)"
            echo "💡 Use grep_filter to narrow down results"
        fi
    }

    # Function to format events with limits
    format_events() {
        local name="$1"
        
        echo -e "\n📅 Recent Events:"
        echo "=============="
        
        kubectl get events --field-selector "involvedObject.name=$name,involvedObject.kind=Node" \
            --sort-by='.lastTimestamp' > "$temp_file"
            
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "No matching events found"
                return
            fi
            echo "$filtered_output" > "$temp_file"
        fi
        
        # Show limited events with formatting
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_EVENTS | awk '{
            if ($7 ~ /Warning/) emoji="⚠️";
            else if ($7 ~ /Normal/) emoji="ℹ️";
            else emoji="📝";
            print "  " emoji " " $0;
        }'
        
        total_events=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_events -gt $MAX_EVENTS ]; then
            echo "⚠️ Event output truncated (showing $MAX_EVENTS of $total_events events)"
        fi
    }

    # Ensure required parameters are provided
    if [ -z "${action}" ]; then
        echo "❌ Error: action is required"
        rm "$temp_file"
        exit 1
    fi

    case "${action}" in
        get)
            if [ -z "${name}" ]; then
                # List all nodes with limits
                echo "📊 Node List:"
                echo "==========="
                kubectl get nodes -o wide | show_resource_status "kubectl get nodes -o wide" "Nodes" "all"
            else
                # Show specific node details
                echo "📊 Node Details:"
                echo "============="
                show_resource_status "kubectl get node ${name} -o wide" "Node" "${name}"
                
                # Show node description
                echo -e "\n📋 Node Description:"
                echo "================="
                show_resource_status "kubectl describe node ${name}" "Node description" "${name}"
                
                # Show node events
                format_events "${name}"
                
                # Show pods running on the node
                echo -e "\n📦 Pods on Node:"
                echo "============="
                kubectl get pods --all-namespaces --field-selector spec.nodeName=${name} > "$temp_file"
                
                # Apply grep filter if provided
                if [ ! -z "$grep_filter" ]; then
                    filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
                    if [ ! -z "$filtered_output" ]; then
                        echo "$filtered_output" > "$temp_file"
                    else
                        echo "No matching pods found"
                    fi
                fi
                
                # Show limited pod list
                head -n 1 "$temp_file"  # Show header
                tail -n +2 "$temp_file" | head -n $MAX_PODS | awk '{
                    status=$4;
                    emoji="❓";
                    if (status == "Running") emoji="✅";
                    else if (status == "Pending") emoji="⏳";
                    else if (status == "Succeeded") emoji="🎉";
                    else if (status == "Failed") emoji="❌";
                    print "  " emoji " " $0;
                }'
                
                total_pods=$(( $(wc -l < "$temp_file") - 1 ))
                if [ $total_pods -gt $MAX_PODS ]; then
                    echo "⚠️ Pod list truncated (showing $MAX_PODS of $total_pods pods)"
                fi
            fi
            ;;
            
        cordon)
            if [ -z "${name}" ]; then
                echo "❌ Error: node name is required for cordon action"
                rm "$temp_file"
                exit 1
            fi
            
            echo "🔒 Cordoning node ${name}..."
            if ! kubectl cordon "${name}"; then
                echo "❌ Failed to cordon node ${name}"
                rm "$temp_file"
                exit 1
            fi
            echo "✅ Successfully cordoned node ${name}"
            
            # Show updated node status
            show_resource_status "kubectl get node ${name} -o wide" "Node" "${name}"
            ;;
            
        uncordon)
            if [ -z "${name}" ]; then
                echo "❌ Error: node name is required for uncordon action"
                rm "$temp_file"
                exit 1
            fi
            
            echo "🔓 Uncordoning node ${name}..."
            if ! kubectl uncordon "${name}"; then
                echo "❌ Failed to uncordon node ${name}"
                rm "$temp_file"
                exit 1
            fi
            echo "✅ Successfully uncordoned node ${name}"
            
            # Show updated node status
            show_resource_status "kubectl get node ${name} -o wide" "Node" "${name}"
            ;;
            
        drain)
            if [ -z "${name}" ]; then
                echo "❌ Error: node name is required for drain action"
                rm "$temp_file"
                exit 1
            fi
            
            echo "🚰 Draining node ${name}..."
            if ! kubectl drain "${name}" --ignore-daemonsets --delete-emptydir-data; then
                echo "❌ Failed to drain node ${name}"
                rm "$temp_file"
                exit 1
            fi
            echo "✅ Successfully drained node ${name}"
            
            # Show updated node status
            show_resource_status "kubectl get node ${name} -o wide" "Node" "${name}"
            ;;
            
        *)
            echo "❌ Error: Invalid action. Supported actions are get, cordon, uncordon, drain"
            rm "$temp_file"
            exit 1
            ;;
    esac

    # Cleanup
    rm "$temp_file"
    ''',
    args=[
        Arg(name="action", type="str", description="Action to perform (get, cordon, uncordon, drain)", required=True),
        Arg(name="name", type="str", description="Name of the node (optional for 'get' action)", required=False),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

node_metrics_tool = KubernetesTool(
    name="node_metrics",
    description="Shows detailed node metrics and resource usage",
    content='''
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)

    # Function to show metrics with limits
    show_metrics() {
        local cmd="$1"
        local metric_type="$2"
        
        if ! eval "$cmd" > "$temp_file"; then
            echo "❌ Failed to get $metric_type metrics"
            rm "$temp_file"
            exit 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $metric_type with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return
            fi
            echo "$filtered_output" > "$temp_file"
        fi
        
        # Show header and limited output
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES | awk '{
            usage=$3;
            if (usage ~ /%/) {
                percentage = substr(usage, 1, length(usage)-1) + 0;
                if (percentage >= 90) emoji="🔴";
                else if (percentage >= 70) emoji="🟡";
                else emoji="🟢";
            } else {
                emoji="📊";
            }
            print "  " emoji " " $0;
        }'
        
        # Show truncation message if needed
        total_lines=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines entries)"
            echo "💡 Use grep_filter to narrow down results"
        fi
    }

    echo "📊 Node Metrics:"
    echo "============="

    if [ ! -z "${name}" ]; then
        # Show metrics for specific node
        show_metrics "kubectl top node ${name}" "Node"
        
        # Show detailed resource allocation
        echo -e "\n💾 Resource Allocation:"
        echo "==================="
        show_metrics "kubectl describe node ${name} | grep -A 5 'Allocated resources'" "Resource allocation"
    else
        # Show metrics for all nodes
        show_metrics "kubectl top nodes" "Nodes"
    fi

    # Cleanup
    rm "$temp_file"
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the node (optional)", required=False),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

# Register tools
for tool in [node_management_tool, node_metrics_tool]:
    tool_registry.register("kubernetes", tool) 