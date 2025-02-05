from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry
import sys

# Constants for output limiting
MAX_OUTPUT_LINES = 100

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes kubectl commands. For namespace-scoped resources, include '-n <namespace>' in the command. Use '--all-namespaces' for cluster-wide queries. Some resources like nodes and persistent volumes are cluster-scoped and don't require a namespace.",
    content="""
    #!/bin/bash
    set -e

    # Create temp file for output management
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT

    # Show the command being executed
    echo "🔧 Executing: kubectl $command"

    # Run the command and capture output
    if ! kubectl $command > "$temp_file"; then
        echo "❌ Command failed: kubectl $command"
        exit 1
    fi

    total_lines=$(wc -l < "$temp_file")
    
    # Apply grep filter if provided
    if [ ! -z "$grep_filter" ]; then
        echo "🔍 Filtering results with: $grep_filter"
        filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
        if [ -z "$filtered_output" ]; then
            echo "⚠️ No results found matching filter: $grep_filter"
            echo "💡 Try adjusting your filter criteria or check if the resource exists"
            exit 0
        fi
        echo "$filtered_output" > "$temp_file"
        filtered_lines=$(wc -l < "$temp_file")
        echo "Found $filtered_lines matching entries"
    fi

    # Show header if present (preserve column headers)
    if head -n 1 "$temp_file" | grep -q "NAME\\|NAMESPACE\\|STATUS\\|AGE"; then
        head -n 1 "$temp_file"
        tail -n +2 "$temp_file" | head -n $MAX_OUTPUT_LINES
    else
        head -n $MAX_OUTPUT_LINES "$temp_file"
    fi

    # Show truncation and help message if needed
    if [ $total_lines -gt $MAX_OUTPUT_LINES ]; then
        echo ""
        echo "⚠️ Output was truncated (showing $MAX_OUTPUT_LINES of $total_lines lines)"
        echo "💡 Tips to narrow down results:"
        echo "   - Add a namespace: -n <namespace>"
        echo "   - Use labels: -l key=value"
        echo "   - Add field selectors: --field-selector=status.phase=Running"
        echo "   - Use grep_filter parameter to search for specific terms"
        echo "   - Remove headers: --no-headers"
        echo "   - For pods: specify container name with -c <container>"
        
        # Context-specific tips based on the command
        if [[ "$command" == *"get pods"* ]]; then
            echo "   - Filter by pod status: --field-selector=status.phase=Running"
            echo "   - Show only pod names: --template '{{range .items}}{{.metadata.name}}{{\"\\n\"}}{{end}}'"
        elif [[ "$command" == *"get nodes"* ]]; then
            echo "   - Filter ready nodes: --field-selector=status.phase=Ready"
            echo "   - Show node capacity: -o custom-columns=NAME:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory"
        elif [[ "$command" == *"get deployments"* ]]; then
            echo "   - Show only available: --field-selector=status.availableReplicas>0"
            echo "   - Custom view: -o custom-columns=NAME:.metadata.name,REPLICAS:.status.replicas,AVAILABLE:.status.availableReplicas"
        fi
    fi

    echo "✅ Command executed successfully"
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

try:
    tool_registry.register("kubernetes", kubectl_tool)
except Exception as e:
    print(f"❌ Failed to register kubectl tool: {str(e)}", file=sys.stderr)
    raise
