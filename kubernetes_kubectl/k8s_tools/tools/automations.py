from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

find_resource_tool = KubernetesTool(
    name="find_resource",
    description="Searches for and lists Kubernetes resources based on type, namespace, labels, and other criteria. Use this for general resource discovery, not for checking specific deployment details.",
    content="""
    #!/bin/bash
    set -e

    # Ensure optional parameters are set to empty strings if not provided
    namespace=${namespace:-}
    label_selector=${label_selector:-}
    field_selector=${field_selector:-}
    search_term=${search_term:-}

    # Use --all-namespaces if no specific namespace is provided
    namespace_flag=$( [ -n "$namespace" ] && echo "-n $namespace" || echo "--all-namespaces" )

    # Run kubectl command and filter by search_term if provided
    result=$(kubectl get $resource_type $namespace_flag \
    $( [ -n "$label_selector" ] && echo "-l $label_selector" ) \
    $( [ -n "$field_selector" ] && echo "--field-selector=$field_selector" ) \
    -o wide | { [ -z "$search_term" ] && cat || grep -i "$search_term"; } || true)

    if [ -z "$result" ]; then
        echo "🔍 No resources found matching the criteria"
    else
        echo "🔍 Found resources:"
        echo "$result" | awk '{print "  • " $0}'
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource to find (e.g., pods, services, deployments)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
        Arg(name="label_selector", type="str", description="Label selector for filtering resources", required=False),
        Arg(name="field_selector", type="str", description="Field selector for filtering resources", required=False),
        Arg(name="search_term", type="str", description="Search term to filter results", required=False),
    ],
)

change_replicas_tool = KubernetesTool(
    name="change_replicas",
    description="Modifies the number of replicas for a specific Kubernetes resource like deployments or statefulsets. Use this to scale up or down a resource.",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace to scale the resource."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Attempt to scale the resource
    if kubectl scale "$resource_type/$resource_name" --replicas="$replicas" $namespace_flag; then
        echo "✅ Successfully changed replicas for $resource_type/$resource_name to $replicas in namespace $namespace"
    else
        echo "❌ Failed to change replicas for $resource_type/$resource_name in namespace $namespace"
        exit 1
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., deployment, statefulset)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)


get_resource_events_tool = KubernetesTool(
    name="get_resource_events",
    description="Fetches the last events for a Kubernetes resource in a specific namespace",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace to fetch resource events."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Check if resource exists and fetch events
    if kubectl get "$resource_type" "$resource_name" $namespace_flag > /dev/null 2>&1; then
        events=$(kubectl describe "$resource_type" "$resource_name" $namespace_flag | sed -n '/Events:/,$p')
        if [ -z "$events" ]; then
            echo "📅 No events found for $resource_type/$resource_name in namespace $namespace"
        else
            echo "📅 Events for $resource_type/$resource_name in namespace $namespace:"
            echo "$events" | sed 's/^/  /'
        fi
    else
        echo "❗Error: $resource_type/$resource_name not found in namespace $namespace"
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., pod, deployment)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),  # Marked as required
    ],
)

get_resource_logs_tool = KubernetesTool(
    name="get_resource_logs",
    description="Fetches logs for a Kubernetes resource, primarily for pods or other resources with log outputs (e.g., pods, containers within pods). Supports optional selection of containers for multi-container resources.",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace to fetch logs."
        exit 1
    fi

    # Ensure optional parameters are set to empty strings if not provided
    container=${container:-}
    previous=${previous:-}
    tail=${tail:-}

    # Set flags for optional parameters
    namespace_flag="-n $namespace"
    container_flag=$( [ -n "$container" ] && echo "-c $container" || echo "" )
    previous_flag=$( [ "$previous" = "true" ] && echo "-p" || echo "" )
    tail_flag=$( [ -n "$tail" ] && echo "--tail=$tail" || echo "" )

    # Fetch logs for the specified resource
    logs=$(kubectl logs $resource_type/$resource_name $namespace_flag $container_flag $previous_flag $tail_flag 2>/dev/null || echo "NotFound")

    if [ "$logs" = "NotFound" ]; then
        echo "❗Error: Logs for $resource_type/$resource_name not found in namespace $namespace"
    elif [ -z "$logs" ]; then
        echo "📜 No logs found for $resource_type/$resource_name in namespace $namespace"
    else
        echo "📜 Logs for $resource_type/$resource_name in namespace $namespace:"
        echo "$logs" | sed 's/^/  /'
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., pod, deployment)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),  # Marked as required
        Arg(name="container", type="str", description="Container name (for multi-container pods)", required=False),
        Arg(name="previous", type="bool", description="Fetch logs from previous terminated container", required=False),
        Arg(name="tail", type="int", description="Number of lines to show from the end of the logs", required=False),
    ],
)


node_status_tool = KubernetesTool(
    name="node_status",
    description="Lists Kubernetes nodes with their status and emojis",
    content="""
    #!/bin/bash
    set -e
    echo "🖥️  Node Status:"
    echo "==============="
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason | 
    awk 'NR>1 {
        status = $2;
        emoji = "❓";
        if (status == "Ready") emoji = "✅";
        else if (status == "NotReady") emoji = "❌";
        else if (status == "SchedulingDisabled") emoji = "🚫";
        print "  " emoji " " $0;
    }'
    """,
    args=[],
)

find_suspicious_errors_tool = KubernetesTool(
    name="find_suspicious_errors",
    description="Finds suspicious errors in a specific Kubernetes namespace or across all namespaces if 'all' is provided.",
    content="""
    #!/bin/sh
    set -e

    # Namespace is required and either a specific namespace or 'all' for all namespaces
    if [ "$namespace" = "all" ]; then
        echo "🔍 Searching for suspicious errors in all namespaces"
        namespace_flag="--all-namespaces"
    else
        echo "🔍 Searching for suspicious errors in namespace: $namespace"
        namespace_flag="-n $namespace"
    fi

    echo "========================================================="
    kubectl get events $namespace_flag --sort-by=.metadata.creationTimestamp | 
    grep -E "Error|Failed|CrashLoopBackOff|Evicted|OOMKilled" |
    tail -n 20 | 
    awk '{
        if ($7 ~ /Error/) emoji = "❌";
        else if ($7 ~ /Failed/) emoji = "💔";
        else if ($7 ~ /CrashLoopBackOff/) emoji = "🔁";
        else if ($7 ~ /Evicted/) emoji = "👉";
        else if ($7 ~ /OOMKilled/) emoji = "💥";
        else emoji = "⚠️";
        print "  " emoji " " $0;
    }'

    echo "\n⚠️  Pods with non-Running status:"
    kubectl get pods $namespace_flag --field-selector status.phase!=Running | 
    awk 'NR>1 {
        status = $3;
        emoji = "❓";
        if (status == "Pending") emoji = "⏳";
        else if (status == "Succeeded") emoji = "🎉";
        else if (status == "Failed") emoji = "❌";
        else if (status == "Unknown") emoji = "❔";
        print "  " emoji " " $0;
    }'
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to search for errors. Use 'all' to search in all namespaces.", required=True),
    ],
)


network_policy_analyzer_tool = KubernetesTool(
    name="network_policy_analyzer",
    description="Analyzes network policies in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "🔒 Network Policy Analysis:"
    echo "========================"
    kubectl get networkpolicies --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,PODS:.spec.podSelector.matchLabels | 
    kubectl get networkpolicies --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,PODS:.spec.podSelector.matchLabels
    echo "\nPods without Network Policies:"
    kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,LABELS:.metadata.labels | 
    awk 'NR>1 {print $1, $2}' | 
    while read ns pod; do
        if ! kubectl get networkpolicies -n $ns -o jsonpath='{.items[*].spec.podSelector.matchLabels}' | grep -q $(kubectl get pod $pod -n $ns -o jsonpath='{.metadata.labels}'); then
            echo "$ns/$pod"
        fi
    done
    """,
    args=[],
)

persistent_volume_usage_tool = KubernetesTool(
    name="persistent_volume_usage",
    description="Shows usage of persistent volumes in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Persistent Volume Usage:"
    echo "========================"
    kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,USED:.status.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name,NAMESPACE:.spec.claimRef.namespace
    """,
    args=[],
)

ingress_analyzer_tool = KubernetesTool(
    name="ingress_analyzer",
    description="Analyzes ingress resources in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Ingress Analysis:"
    echo "================="
    kubectl get ingress --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,HOSTS:.spec.rules[*].host,PATHS:.spec.rules[*].http.paths[*].path,SERVICES:.spec.rules[*].http.paths[*].backend.service.name
    """,
    args=[],
)

resource_quota_usage_tool = KubernetesTool(
    name="resource_quota_usage",
    description="Shows resource quota usage across namespaces",
    content="""
    #!/bin/bash
    set -e
    echo "Resource Quota Usage:"
    echo "====================="
    kubectl get resourcequota --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,RESOURCE:.spec.hard,USED:.status.used
    """,
    args=[],
)

cluster_autoscaler_status_tool = KubernetesTool(
    name="cluster_autoscaler_status",
    description="Checks the status of the cluster autoscaler",
    content="""
    #!/bin/bash
    set -e
    echo "Cluster Autoscaler Status:"
    echo "=========================="
    kubectl get deployments -n kube-system | grep cluster-autoscaler
    echo "\nCluster Autoscaler Logs:"
    kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
    """,
    args=[],
)

pod_disruption_budget_checker_tool = KubernetesTool(
    name="pod_disruption_budget_checker",
    description="Checks Pod Disruption Budgets (PDBs) in the cluster, across all namespaces or filtered by a specific namespace.",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag if provided, or default to all namespaces
    namespace_flag=${namespace:---all-namespaces}

    echo "Pod Disruption Budgets:"
    echo "======================="
    
    if ! kubectl get pdb $namespace_flag -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,MIN-AVAILABLE:.spec.minAvailable,MAX-UNAVAILABLE:.spec.maxUnavailable,ALLOWED-DISRUPTIONS:.status.disruptionsAllowed; then
        echo "❌ Error: Failed to retrieve Pod Disruption Budgets. Please check permissions and kubectl availability."
        exit 1
    fi
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to filter results. If omitted, checks all namespaces.", required=False),
    ],
)

check_replicas_tool = KubernetesTool(
    name="check_replicas",
    description="Retrieves the current number of replicas for a specific Kubernetes deployment or statefulset. Requires specifying a namespace.",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required for checking replicas of $resource_type/$resource_name."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Get the number of replicas
    replicas=$(kubectl get $resource_type $resource_name $namespace_flag -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "NotFound")

    if [ "$replicas" = "NotFound" ]; then
        echo "❗Error: $resource_type/$resource_name not found in namespace $namespace."
    else
        echo "Current number of replicas for $resource_type/$resource_name: $replicas"
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., deployment, statefulset)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

# Register all tools
for tool in [
    find_resource_tool,
    change_replicas_tool,
    get_resource_events_tool,
    get_resource_logs_tool,
    node_status_tool,
    find_suspicious_errors_tool,
    network_policy_analyzer_tool,
    persistent_volume_usage_tool,
    ingress_analyzer_tool,
    resource_quota_usage_tool,
    cluster_autoscaler_status_tool,
    pod_disruption_budget_checker_tool,
    check_replicas_tool,
]:
    tool_registry.register("kubernetes", tool)