from kubiya_workflow_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_workflow_sdk.tools.registry import tool_registry

namespace_tool = KubernetesTool(
    name="list_namespaces",
    description="Lists all Kubernetes namespaces in the cluster",
    content="""
    #!/bin/bash
    set -e

    # Execute kubectl get namespaces command
    full_command="kubectl get namespaces"

    # Show the command being executed
    echo "🔍 Listing all namespaces..."

    # Run the kubectl command
    if output=$(eval "$full_command"); then
        echo "✅ Namespaces retrieved successfully:"
        echo "$output"
    else
        echo "❌ Failed to retrieve namespaces"
        exit 1
    fi
    """,
    args=[],  # No arguments needed since this tool has a single purpose
)

tool_registry.register("kubernetes", namespace_tool)