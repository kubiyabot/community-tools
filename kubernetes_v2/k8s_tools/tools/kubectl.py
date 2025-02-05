from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry
import sys

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes kubectl commands. For namespace-scoped resources, include '-n <namespace>' in the command. Use '--all-namespaces' for cluster-wide queries. Some resources like nodes and persistent volumes are cluster-scoped and don't require a namespace.",
    content="""
    #!/bin/bash
    set -e

    # Show the command being executed
    echo "🔧 Executing: kubectl $command"

    # Create a temporary file to store the full output
    temp_file=$(mktemp)
    
    # Run the command and capture full output
    if kubectl $command > "$temp_file"; then
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
        
        # Show limited output
        head -n 100 "$temp_file"
        
        # Provide helpful feedback about results
        if [ $total_lines -gt 100 ]; then
            echo ""
            echo "⚠️ Output was truncated (showing 100 of $total_lines lines)"
            echo "💡 Tips to narrow down results:"
            echo "   - Add a namespace: -n <namespace>"
            echo "   - Use labels: -l key=value"
            echo "   - Add field selectors: --field-selector=status.phase=Running"
            echo "   - Use grep filter to search: add grep_filter parameter"
            echo "   - Remove headers: --no-headers"
        fi
        
        echo "✅ Command executed successfully"
    else
        echo "❌ Command failed: kubectl $command"
        rm "$temp_file"
        exit 1
    fi
    
    # Cleanup
    rm "$temp_file"
    """,
    args=[
        Arg(
            name="command", 
            type="str", 
            description="The full kubectl command to execute. Examples include (but are not limited to):\n" +
                       "- 'get pods -n default'\n" +
                       "- 'create namespace test'\n" +
                       "- 'get pods --all-namespaces'\n" +
                       "- 'get nodes'  # cluster-scoped resource, no namespace needed\n" +
                       "- 'describe node my-node-1'",
            required=True
        ),
        Arg(
            name="grep_filter",
            type="str",
            description="Optional case-insensitive grep pattern to filter results (e.g., 'running' to show only running pods)",
            required=False
        ),
    ],
)

tool_registry.register("kubernetes", kubectl_tool)