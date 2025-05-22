from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

single_pod_operations_tool = KubernetesTool(
    name="single_pod_operations",
    description="Performs operations on a single Kubernetes pod - retrieves logs, gets detailed information, or deletes a specific pod.",
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
        Arg(name="action", type="str", description="Action to perform on a single pod (get, delete, logs)", required=True),
        Arg(name="name", type="str", description="Name of the specific pod to operate on", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace where the pod is located", required=True),
        Arg(name="container", type="str", description="Container name (only used for logs action)", required=False),
    ],
)

bulk_pod_operations_tool = KubernetesTool(
    name="bulk_pod_operations",
    description="Performs operations on multiple Kubernetes pods - list, delete, or filter pods across namespaces",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag based on input
    if [ -n "${namespace:-}" ]; then
        namespace_flag="-n $namespace"
        check_all_namespaces=false
    else
        namespace_flag="--all-namespaces"
        check_all_namespaces=true
    fi
    
    # Set selector flag if provided
    selector="${selector:-}"
    selector_flag=""
    if [ -n "$selector" ]; then
        selector_flag="-l $selector"
    fi
    
    # Set field selector if provided
    field_selector="${field_selector:-}"
    field_selector_flag=""
    if [ -n "$field_selector" ]; then
        field_selector_flag="--field-selector=$field_selector"
    fi

    if [ "$action" = "get" ]; then
        kubectl get pods $namespace_flag $selector_flag $field_selector_flag
    elif [ "$action" = "delete" ]; then
        if [ -z "$selector" ] && [ -z "$field_selector" ]; then
            echo "❌ Error: Either label selector or field selector is required for bulk delete operations for safety"
            exit 1
        fi
        kubectl delete pods $namespace_flag $selector_flag $field_selector_flag
    fi
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (get, delete)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace to filter results. If omitted, shows all namespaces", required=False),
        Arg(name="selector", type="str", description="Label selector to filter pods (e.g. 'app=myapp')", required=False),
        Arg(name="field_selector", type="str", description="Field selector to filter pods (e.g. 'status.phase=Failed')", required=False),
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
    single_pod_operations_tool,
    bulk_pod_operations_tool,
    check_pod_restarts_tool,
]:
    tool_registry.register("kubernetes", tool)