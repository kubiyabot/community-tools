from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_usage_tool = KubernetesTool(
    name="resource_usage",
    description="Shows resource usage of nodes or pods, requiring a namespace or 'all' for all namespaces",
    content="""
    #!/bin/bash
    set -e

    # Create a temporary file to store the full output
    temp_file=$(mktemp)

    # Ensure resource type is either 'nodes' or 'pods'
    if [ "$resource_type" != "nodes" ] && [ "$resource_type" != "pods" ]; then
        echo "❌ Invalid resource type. Use 'nodes' or 'pods'."
        rm "$temp_file"
        exit 1
    fi

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Namespace is required. Please specify a namespace or 'all' for all namespaces."
        rm "$temp_file"
        exit 1
    fi

    # Set namespace flag
    namespace_flag=$( [ "$namespace" = "all" ] && echo "--all-namespaces" || echo "-n $namespace" )

    if [ "$resource_type" = "nodes" ]; then
        echo "🖥️  Node Resource Usage:"
        echo "======================="
        kubectl top nodes > "$temp_file"
    elif [ "$resource_type" = "pods" ]; then
        echo "🛠️  Pod Resource Usage:"
        echo "====================="
        kubectl top pods $namespace_flag > "$temp_file"
    fi

    total_lines=$(wc -l < "$temp_file")
    
    # Apply grep filter if provided
    if [ ! -z "$grep_filter" ]; then
        echo "🔍 Filtering results with: $grep_filter"
        filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
        echo "$filtered_output" > "$temp_file"
        filtered_lines=$(wc -l < "$temp_file")
        if [ $filtered_lines -eq 0 ]; then
            echo "⚠️ No results found matching filter: $grep_filter"
            echo "💡 Try adjusting your filter criteria or check if the resource exists"
            rm "$temp_file"
            exit 0
        fi
    fi

    # Show header and limited output
    head -n 1 "$temp_file"  # Always show header
    tail -n +2 "$temp_file" | head -n 100 | awk 'NR>0 {print "  🔧 " $0}'

    # Show truncation message if needed
    if [ $total_lines -gt 101 ]; then  # +1 for header
        echo ""
        echo "⚠️ Output was truncated (showing 100 of $((total_lines-1)) entries)"
        echo "💡 Tips to narrow down results:"
        echo "   - Use grep_filter to search for specific terms"
        echo "   - Specify a particular namespace"
        [ "$resource_type" = "pods" ] && echo "   - Use labels with kubectl top pods -l key=value"
    fi

    rm "$temp_file"
    """,
    args=[
        Arg(name="resource_type", type="str", description="Resource type to show usage for (nodes or pods)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace or 'all' for all namespaces", required=True),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

cluster_health_tool = KubernetesTool(
    name="cluster_health",
    description="Provides a summary of the Kubernetes cluster health",
    content="""
    #!/bin/bash
    set -e
    
    temp_file=$(mktemp)
    
    echo "🏥 Cluster Health Summary:"
    echo "========================="
    
    # Function to process and display limited results
    process_output() {
        local section_name=$1
        local total_lines=$(wc -l < "$temp_file")
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $section_name with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            echo "$filtered_output" > "$temp_file"
            if [ ! -s "$temp_file" ]; then
                echo "⚠️ No results found in $section_name matching filter: $grep_filter"
                return
            fi
        fi
        
        # Show header and limited output
        head -n 1 "$temp_file"  # Always show header
        tail -n +2 "$temp_file" | head -n 25  # Show 25 entries per section
        
        # Show truncation message if needed
        if [ $total_lines -gt 26 ]; then  # +1 for header
            echo "⚠️ Output truncated (showing 25 of $((total_lines-1)) entries)"
        fi
        echo ""
    }
    
    echo "🖥️  Node Status:"
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason > "$temp_file"
    process_output "Nodes"
    
    echo "🛠️  Pod Status:"
    kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName > "$temp_file"
    process_output "Pods"
    
    echo "🚀 Deployment Status:"
    kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,DESIRED:.spec.replicas,AVAILABLE:.status.availableReplicas,UP-TO-DATE:.status.updatedReplicas > "$temp_file"
    process_output "Deployments"
    
    echo "💾 Persistent Volume Status:"
    kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name > "$temp_file"
    process_output "Persistent Volumes"
    
    if [ $total_lines -gt 26 ]; then
        echo "💡 Tips to narrow results:"
        echo "   - Use grep_filter to search for specific terms"
        echo "   - Use kubectl directly with labels or field selectors for more specific queries"
    fi
    
    rm "$temp_file"
    """,
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results across all sections", required=False),
    ],
)

cluster_insights_tool = KubernetesTool(
    name="cluster_insights",
    description="Provides insights about the Kubernetes cluster",
    content='''
    #!/bin/bash
    set -e
    
    temp_file=$(mktemp)
    
    echo "🔍 Gathering cluster insights..."
    
    # Get cluster info
    if ! kubectl cluster-info > "$temp_file" 2>&1; then
        echo "❌ Failed to get cluster info"
        rm "$temp_file"
        exit 1
    fi
    
    # Apply grep filter to cluster info if provided
    if [ ! -z "$grep_filter" ]; then
        filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
        if [ ! -z "$filtered_output" ]; then
            echo "$filtered_output"
        fi
    else
        cat "$temp_file"
    fi
    
    # Get node status with limits
    echo -e "\n📊 Node Status:"
    kubectl get nodes -o wide > "$temp_file"
    head -n 1 "$temp_file"  # Show header
    if [ ! -z "$grep_filter" ]; then
        tail -n +2 "$temp_file" | grep -i "$grep_filter" | head -n 25 || echo "No matching nodes found"
    else
        tail -n +2 "$temp_file" | head -n 25
    fi
    
    total_nodes=$(( $(wc -l < "$temp_file") - 1 ))
    if [ $total_nodes -gt 25 ]; then
        echo "⚠️ Node output truncated (showing 25 of $total_nodes nodes)"
    fi
    
    # Get namespace resource usage with limits
    echo -e "\n📈 Namespace Resource Usage:"
    namespaces=$(kubectl get ns --no-headers | awk '{print $1}' | head -n 10)
    
    if [ ! -z "$grep_filter" ]; then
        namespaces=$(echo "$namespaces" | grep -i "$grep_filter" || true)
        if [ -z "$namespaces" ]; then
            echo "No matching namespaces found"
            rm "$temp_file"
            exit 0
        fi
    fi
    
    for ns in $namespaces; do
        echo "Namespace: ${ns}"
        kubectl top pod -n "${ns}" > "$temp_file" 2>/dev/null || echo "  No metrics available"
        if [ -s "$temp_file" ]; then
            head -n 1 "$temp_file"  # Show header
            if [ ! -z "$grep_filter" ]; then
                tail -n +2 "$temp_file" | grep -i "$grep_filter" | head -n 10 || echo "  No matching pods found"
            else
                tail -n +2 "$temp_file" | head -n 10
            fi
            total_pods=$(( $(wc -l < "$temp_file") - 1 ))
            if [ $total_pods -gt 10 ]; then
                echo "⚠️ Pod output truncated (showing 10 of $total_pods pods)"
            fi
        fi
    done
    
    total_ns=$(kubectl get ns --no-headers | wc -l)
    if [ $(echo "$namespaces" | wc -l) -lt $total_ns ]; then
        echo "\n⚠️ Namespace list truncated (showing 10 of $total_ns namespaces)"
        echo "💡 Tips to narrow results:"
        echo "   - Use grep_filter to search for specific terms"
        echo "   - Use kubectl top directly for specific namespaces"
    fi
    
    rm "$temp_file"
    ''',
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

# Register all tools
for tool in [
    resource_usage_tool,
    cluster_health_tool,
    cluster_insights_tool,
]:
    tool_registry.register("kubernetes", tool)
