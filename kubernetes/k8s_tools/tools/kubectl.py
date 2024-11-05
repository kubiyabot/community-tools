from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes kubectl commands within a specific namespace or across all namespaces",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided or specify 'all' for all namespaces."
        exit 1
    fi

    # If namespace is 'all', use the --all-namespaces flag, otherwise use the specific namespace
    if [ "$namespace" = "all" ]; then
        full_command="kubectl $command --all-namespaces"
    else
        full_command="kubectl $command -n $namespace"
    fi

    # Show the command being executed
    echo "🔧 Executing: $full_command"

    # Run the kubectl command
    if eval "$full_command"; then
        echo "✅ Command executed successfully"
    else
        echo "❌ Command failed: $full_command"
        exit 1
    fi
    """,
    args=[
        Arg(name="command", type="str", description="The kubectl command to execute", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace or 'all' for all namespaces", required=True),  # Required
    ],
)


tool_registry.register("kubernetes", kubectl_tool)
