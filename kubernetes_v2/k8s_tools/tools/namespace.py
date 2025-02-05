from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Constants for output limiting
MAX_OUTPUT_LINES = 50
MAX_EVENTS = 25

namespace_tool = KubernetesTool(
    name="list_namespaces",
    description="Lists and manages Kubernetes namespaces in the cluster",
    content=f'''
    #!/bin/bash
    set -e

    # Constants
    MAX_OUTPUT_LINES={MAX_OUTPUT_LINES}
    MAX_EVENTS={MAX_EVENTS}

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Function to show resource status with limits
    show_resource_status() {{
        local cmd="$1"
        local description="$2"
        
        if ! eval "$cmd" > "$temp_file"; then
            echo "❌ Failed to get $description"
            exit 1
        fi
        
        # Get grep_filter value safely
        grep_filter=$(get_param "grep_filter")
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            echo "🔍 Filtering $description with: $grep_filter"
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ -z "$filtered_output" ]; then
                echo "⚠️ No matches found for filter: $grep_filter"
                return
            fi
            echo "$filtered_output" > "$temp_file"
            filtered_lines=$(wc -l < "$temp_file")
            echo "Found $filtered_lines matching entries"
        fi
        
        # Show header and limited output
        head -n 1 "$temp_file"  # Show header
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES | awk '{{
            status=$2;
            emoji="ℹ️";
            if (status == "Active") emoji="✅";
            else if (status == "Terminating") emoji="🔄";
            print "  " emoji " " $0;
        }}'
        
        # Show truncation message if needed
        total_lines=$(( $(wc -l < "$temp_file") - 1 ))
        if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
            echo ""
            echo "⚠️ Output truncated (showing $MAX_OUTPUT_LINES of $total_lines namespaces)"
            echo "💡 Tips to narrow down results:"
            echo "   - Use grep_filter to search for specific namespaces"
            echo "   - Use labels: kubectl get ns -l key=value"
            echo "   - Use field selectors: --field-selector status.phase=Active"
        fi
    }}

    # Function to show namespace details
    show_namespace_details() {{
        local ns="$1"
        
        echo "📊 Namespace Details:"
        echo "=================="
        kubectl describe namespace "$ns" > "$temp_file"
        
        # Get grep_filter value safely
        grep_filter=$(get_param "grep_filter")
        
        # Apply grep filter if provided
        if [ ! -z "$grep_filter" ]; then
            filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
            if [ ! -z "$filtered_output" ]; then
                echo "$filtered_output"
            else
                echo "No matching details found"
            fi
        else
            cat "$temp_file"
        fi
        
        # Show resource quotas
        echo -e "\n💼 Resource Quotas:"
        echo "================="
        if kubectl get resourcequota -n "$ns" > "$temp_file" 2>/dev/null; then
            show_resource_status "kubectl get resourcequota -n $ns" "resource quotas"
        else
            echo "No resource quotas defined"
        fi
        
        # Show limit ranges
        echo -e "\n📊 Limit Ranges:"
        echo "=============="
        if kubectl get limitrange -n "$ns" > "$temp_file" 2>/dev/null; then
            show_resource_status "kubectl get limitrange -n $ns" "limit ranges"
        else
            echo "No limit ranges defined"
        fi
        
        # Show resource summary
        echo -e "\n📈 Resource Usage:"
        echo "==============="
        kubectl top pod -n "$ns" > "$temp_file" 2>/dev/null || echo "No metrics available"
        if [ -s "$temp_file" ]; then
            show_resource_status "kubectl top pod -n $ns" "resource usage"
        fi
    }}

    # Get action parameter with default value 'list'
    action=$(get_param "action" "list")

    case "$action" in
        list)
            echo "🔍 Listing namespaces..."
            show_resource_status "kubectl get namespaces" "namespaces"
            ;;
            
        describe)
            name=$(get_param "name")
            if [ -z "$name" ]; then
                echo "❌ Namespace name is required for describe action"
                exit 1
            fi
            show_namespace_details "$name"
            ;;
            
        create)
            name=$(get_param "name")
            if [ -z "$name" ]; then
                echo "❌ Namespace name is required for create action"
                exit 1
            fi
            echo "🔨 Creating namespace: $name"
            if kubectl create namespace "$name"; then
                echo "✅ Namespace created successfully"
                show_namespace_details "$name"
            else
                echo "❌ Failed to create namespace"
                exit 1
            fi
            ;;
            
        delete)
            name=$(get_param "name")
            if [ -z "$name" ]; then
                echo "❌ Namespace name is required for delete action"
                exit 1
            fi
            echo "🗑️  Deleting namespace: $name"
            if kubectl delete namespace "$name"; then
                echo "✅ Namespace deleted successfully"
            else
                echo "❌ Failed to delete namespace"
                exit 1
            fi
            ;;
            
        *)
            echo "❌ Invalid action. Supported actions are: list, describe, create, delete"
            exit 1
            ;;
    esac
    ''',
    args=[
        Arg(
            name="action",
            type="str",
            description="Action to perform (list, describe, create, delete)",
            required=False
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the namespace (required for describe, create, delete actions)",
            required=False
        ),
        Arg(
            name="grep_filter",
            type="str",
            description="Optional case-insensitive grep pattern to filter results",
            required=False
        ),
    ],
)

tool_registry.register("kubernetes", namespace_tool)