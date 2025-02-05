from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Constants for output limiting
MAX_OUTPUT_LINES = 100
MAX_EVENTS = 25

resource_usage_tool = KubernetesTool(
    name="resource_usage",
    description="Shows resource usage of nodes or pods, requiring a namespace or 'all' for all namespaces",
    content="""
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Ensure resource type is either 'nodes' or 'pods'
    if [ "$resource_type" != "nodes" ] && [ "$resource_type" != "pods" ]; then
        echo "❌ Invalid resource type. Use 'nodes' or 'pods'."
        rm "$temp_file"
        exit 1
    fi

    # Ensure namespace is provided for pods
    if [ "$resource_type" = "pods" ] && [ -z "$namespace" ]; then
        echo "❌ Namespace is required for pods. Please specify a namespace or 'all' for all namespaces."
        rm "$temp_file"
        exit 1
    fi

    # Set namespace flag for pods
    namespace_flag=$( [ "$namespace" = "all" ] && echo "--all-namespaces" || echo "-n $namespace" )

    # Function to show resource usage with limits
    show_resource_usage() {
        local cmd="$1"
        local resource="$2"
        
        if ! eval "$cmd" > "$temp_file"; then
            echo "❌ Failed to get $resource usage"
            return 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $resource with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return 0
            fi
            echo "$filtered_output" > "$temp_file"
            filtered_lines=$(wc -l < "$temp_file")
            echo "Found $filtered_lines matching entries"
        fi
        
        # Show header and limited output with resource indicators
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES | awk '
        function get_usage_emoji(usage) {
            percentage = substr(usage, 1, length(usage)-1) + 0
            if (percentage >= 90) return "🔴"
            else if (percentage >= 70) return "🟡"
            else return "🟢"
        }
        {
            cpu_usage = $3
            mem_usage = $5
            cpu_emoji = get_usage_emoji(cpu_usage)
            mem_emoji = get_usage_emoji(mem_usage)
            printf "  %s CPU:%s MEM:%s %s\n", ($1 ~ /^NAME/ ? "📊" : "🔧"), cpu_emoji, mem_emoji, $0
        }'
        
        # Show truncation message if needed
        total_lines=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo ""
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines entries)"
            echo "💡 Tips to narrow down results:"
            echo "   - Use grep_filter to search for specific resources"
            if [ "$resource_type" = "pods" ]; then
                echo "   - Specify a namespace instead of 'all'"
                echo "   - Use labels: -l key=value"
                echo "   - Filter by status: --field-selector status.phase=Running"
            else
                echo "   - Use node selectors: -l node-role.kubernetes.io/master"
                echo "   - Filter by node condition: --field-selector status.phase=Ready"
            fi
        fi
    }

    if [ "$resource_type" = "nodes" ]; then
        echo "🖥️  Node Resource Usage:"
        echo "======================="
        show_resource_usage "kubectl top nodes" "nodes"
        
        # Show additional node metrics if available
        if command -v crictl >/dev/null 2>&1; then
            echo -e "\n📊 Container Runtime Stats:"
            echo "======================="
            crictl stats --no-trunc > "$temp_file" 2>/dev/null || true
            if [ -s "$temp_file" ]; then
                show_resource_usage "cat $temp_file" "container runtime"
            else
                echo "No container runtime stats available"
            fi
        fi
        
    elif [ "$resource_type" = "pods" ]; then
        echo "🛠️  Pod Resource Usage:"
        echo "====================="
        show_resource_usage "kubectl top pods $namespace_flag" "pods"
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Resource type to show usage for (nodes or pods)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace or 'all' for all namespaces (required for pods)", required=False),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

cluster_health_tool = KubernetesTool(
    name="cluster_health",
    description="Provides a summary of the Kubernetes cluster health",
    content="""
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Function to show resource status with limits
    show_resource_status() {
        local cmd="$1"
        local resource="$2"
        local format_cmd="$3"
        
        if ! eval "$cmd" > "$temp_file"; then
            echo "❌ Failed to get $resource status"
            return 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $resource with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return 0
            fi
            echo "$filtered_output" > "$temp_file"
            filtered_lines=$(wc -l < "$temp_file")
            echo "Found $filtered_lines matching entries"
        fi
        
        # Show header and limited output
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES | eval "$format_cmd"
        
        # Show truncation message if needed
        total_lines=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo ""
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines entries)"
            echo "💡 Use grep_filter to narrow down results"
        fi
    }

    echo "🏥 Cluster Health Summary:"
    echo "========================="

    echo "🖥️  Node Status:"
    show_resource_status \
        "kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason" \
        "nodes" \
        "awk '{
            status = \$2;
            emoji = \"❓\";
            if (status == \"Ready\") emoji = \"✅\";
            else if (status == \"NotReady\") emoji = \"❌\";
            else if (status == \"SchedulingDisabled\") emoji = \"🚫\";
            print \"  \" emoji \" \" \$0;
        }'"

    echo -e "\n🛠️  Pod Status:"
    show_resource_status \
        "kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName" \
        "pods" \
        "awk '{
            status = \$3;
            emoji = \"❓\";
            if (status == \"Running\") emoji = \"✅\";
            else if (status == \"Pending\") emoji = \"⏳\";
            else if (status == \"Succeeded\") emoji = \"🎉\";
            else if (status == \"Failed\") emoji = \"❌\";
            else if (status == \"Unknown\") emoji = \"❔\";
            print \"  \" emoji \" \" \$0;
        }'"

    echo -e "\n🚀 Deployment Status:"
    show_resource_status \
        "kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,DESIRED:.spec.replicas,AVAILABLE:.status.availableReplicas,UP-TO-DATE:.status.updatedReplicas" \
        "deployments" \
        "awk '{
            if (\$3 == \$4 && \$3 == \$5) emoji = \"✅\";
            else if (\$4 == \"0\") emoji = \"❌\";
            else emoji = \"⚠️\";
            print \"  \" emoji \" \" \$0;
        }'"

    echo -e "\n💾 Persistent Volume Status:"
    show_resource_status \
        "kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name" \
        "persistent volumes" \
        "awk '{
            status = \$3;
            emoji = \"❓\";
            if (status == \"Bound\") emoji = \"✅\";
            else if (status == \"Available\") emoji = \"🆓\";
            else if (status == \"Released\") emoji = \"🔓\";
            else if (status == \"Failed\") emoji = \"❌\";
            print \"  \" emoji \" \" \$0;
        }'"
    """,
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

node_metrics_tool = KubernetesTool(
    name="node_metrics",
    description="Provides detailed node metrics including CPU, memory, disk, and network usage",
    content='''
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Function to show metrics with limits
    show_metrics() {
        local cmd="$1"
        local metric_type="$2"
        local format_cmd="${3:-cat}"
        
        if ! eval "$cmd" > "$temp_file" 2>/dev/null; then
            echo "❌ Failed to get $metric_type metrics"
            return 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $metric_type with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return 0
            fi
            echo "$filtered_output" > "$temp_file"
            filtered_lines=$(wc -l < "$temp_file")
            echo "Found $filtered_lines matching entries"
        fi
        
        # Show header and limited output
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES | eval "$format_cmd"
        
        # Show truncation message if needed
        total_lines=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo ""
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines entries)"
            echo "💡 Use grep_filter to narrow down results"
        fi
    }

    # Function to format percentage with emoji
    format_percentage() {
        local value="$1"
        if [ "$value" -ge 90 ]; then
            echo "🔴 $value%"
        elif [ "$value" -ge 70 ]; then
            echo "🟡 $value%"
        else
            echo "🟢 $value%"
        fi
    }

    echo "📊 Node Metrics Overview:"
    echo "======================"

    # Show node resource usage
    echo "💻 CPU and Memory Usage:"
    show_metrics "kubectl top nodes" "resource usage" \
        "awk '{
            if (NR > 1) {
                cpu_usage = substr(\$3, 1, length(\$3)-1);
                mem_usage = substr(\$5, 1, length(\$5)-1);
                cpu_emoji = cpu_usage >= 90 ? \"🔴\" : (cpu_usage >= 70 ? \"🟡\" : \"🟢\");
                mem_emoji = mem_usage >= 90 ? \"🔴\" : (mem_usage >= 70 ? \"🟡\" : \"🟢\");
                printf \"  Node: %s\\n    CPU: %s %s\\n    Memory: %s %s\\n\", \$1, cpu_emoji, \$3, mem_emoji, \$5;
            }
        }'"

    # Show node conditions
    echo -e "\n🏥 Node Health Status:"
    show_metrics "kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[*].type,CONDITION:.status.conditions[*].status" \
        "node health" \
        "awk '{
            if (NR > 1) {
                status = \$2;
                emoji = \"✅\";
                if (status ~ /NotReady/) emoji = \"❌\";
                print \"  \" emoji \" \" \$0;
            }
        }'"

    # Show node capacity and allocatable resources
    echo -e "\n💾 Resource Capacity:"
    show_metrics "kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_CAP:.status.capacity.cpu,CPU_ALLOC:.status.allocatable.cpu,MEM_CAP:.status.capacity.memory,MEM_ALLOC:.status.allocatable.memory,PODS_CAP:.status.capacity.pods" \
        "resource capacity"

    # Show node pressure conditions
    echo -e "\n⚠️  Resource Pressure:"
    show_metrics "kubectl get nodes -o custom-columns=NAME:.metadata.name,DISK_PRESSURE:.status.conditions[?(@.type=='DiskPressure')].status,MEM_PRESSURE:.status.conditions[?(@.type=='MemoryPressure')].status,PID_PRESSURE:.status.conditions[?(@.type=='PIDPressure')].status" \
        "resource pressure" \
        "awk '{
            if (NR > 1) {
                disk_emoji = \$2 == \"False\" ? \"🟢\" : \"🔴\";
                mem_emoji = \$3 == \"False\" ? \"🟢\" : \"🔴\";
                pid_emoji = \$4 == \"False\" ? \"🟢\" : \"🔴\";
                printf \"  Node: %s\\n    Disk Pressure: %s %s\\n    Memory Pressure: %s %s\\n    PID Pressure: %s %s\\n\", 
                    \$1, disk_emoji, \$2, mem_emoji, \$3, pid_emoji, \$4;
            }
        }'"

    # Show node taints and labels
    echo -e "\n🏷️  Node Labels and Taints:"
    show_metrics "kubectl get nodes -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labels,TAINTS:.spec.taints" \
        "node configuration"
    ''',
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

cluster_insights_tool = KubernetesTool(
    name="cluster_insights",
    description="Provides insights about the Kubernetes cluster",
    content='''
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Function to show insights with limits
    show_insights() {
        local cmd="$1"
        local section="$2"
        
        if ! eval "$cmd" > "$temp_file" 2>/dev/null; then
            echo "❌ Failed to get $section"
            return 1
        fi
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $section with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return 0
            fi
            echo "$filtered_output" > "$temp_file"
            filtered_lines=$(wc -l < "$temp_file")
            echo "Found $filtered_lines matching entries"
        fi
        
        # Show limited output
        head -n $MAX_OUTPUT_LINES "$temp_file"
        
        # Show truncation message if needed
        total_lines=$(wc -l < "$temp_file")
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo ""
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines lines)"
            echo "💡 Use grep_filter to narrow down results"
        fi
    }

    echo "🔍 Gathering cluster insights..."

    # Get cluster info
    echo "🌐 Cluster Information:"
    echo "===================="
    show_insights "kubectl cluster-info" "cluster info"

    # Get node status
    echo -e "\n📊 Node Status:"
    echo "============="
    show_insights "kubectl get nodes -o wide" "node status"

    # Get namespace usage
    echo -e "\n📈 Namespace Resource Usage:"
    echo "========================="
    kubectl get ns --no-headers | while read ns _; do
        echo "Namespace: ${ns}"
        kubectl top pod -n "${ns}" > "$temp_file" 2>/dev/null || echo "  No metrics available"
        if [ -s "$temp_file" ]; then
            if [ ! -z "$grep_filter" ]; then
                filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
                if [ ! -z "$filtered_output" ]; then
                    echo "$filtered_output" | head -n $MAX_OUTPUT_LINES
                else
                    echo "  No matching pods found"
                fi
            else
                head -n $MAX_OUTPUT_LINES "$temp_file"
            fi
            
            total_lines=$(wc -l < "$temp_file")
            if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
                echo "  ⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines pods)"
            fi
        fi
    done
    ''',
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

# Register all tools
for tool in [
    resource_usage_tool,
    cluster_health_tool,
    node_metrics_tool,
    cluster_insights_tool,
]:
    tool_registry.register("kubernetes", tool)
