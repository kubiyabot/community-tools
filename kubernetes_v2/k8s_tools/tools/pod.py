from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

pod_management_tool = KubernetesTool(
    name="pod_management",
    description="Manages Kubernetes pods, including retrieving logs, getting information, or deleting a pod.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required to manage a specific pod."
        exit 1
    fi

    # Define namespace and container flags if provided
    namespace_flag="-n $namespace"
    container_flag=$( [ "$action" = "logs" ] && [ -n "$container" ] && echo "-c $container" || echo "" )

    # Execute the action
    if [ "$action" = "logs" ]; then
        kubectl logs "$name" $container_flag $namespace_flag
    else
        kubectl "$action" pod "$name" $namespace_flag
    fi
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (get, delete, logs)", required=True),
        Arg(name="name", type="str", description="Name of the pod", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (required for managing a specific pod)", required=True),
        Arg(name="container", type="str", description="Container name (for logs action)", required=False),
    ],
)


check_pod_restarts_tool = KubernetesTool(
    name="check_pod_restarts",
    description="Checks for pods with high restart counts",
    content="""
    #!/bin/bash
    set -e

    # Set default values for optional parameters
    namespace="${namespace:-}"
    threshold="${threshold:-5}"

    echo "🔄 Pods with high restart counts (threshold: $threshold):"
    echo "======================================================="

    # Set namespace flag if namespace is provided; otherwise, check all namespaces
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    # Fetch pod data and check restart counts
    kubectl get pods $namespace_flag -o json | jq -r \
        '.items[] | 
        .metadata.namespace as $ns | 
        .metadata.name as $pod_name |
        .status.containerStatuses[]? | 
        select(.restartCount >= '"$threshold"') |
        "\($ns) \($pod_name) \(.name) \(if .restartCount >= 20 then "🚨" elif .restartCount >= 10 then "⛔" else "⚠️" end) \(.restartCount) \(.state)"' |
        awk '{print "  " $0}'
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to filter results. If omitted, checks all namespaces.", required=False),
        Arg(name="threshold", type="int", description="Minimum number of restarts to report", required=False),
    ],
)

# Register all tools
for tool in [
    pod_management_tool,
    check_pod_restarts_tool,
]:
    tool_registry.register("kubernetes", tool)