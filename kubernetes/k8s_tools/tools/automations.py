from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

scale_deployment_tool = KubernetesTool(
    name="scale_deployment",
    description="Scales a Kubernetes deployment",
    content="""
    #!/bin/bash
    set -e
    kubectl scale deployment $name --replicas=$replicas $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

find_resource_tool = KubernetesTool(
    name="find_resource",
    description="Finds Kubernetes resources based on filters and search criteria",
    content="""
    #!/bin/bash
    set -e
    kubectl get $resource_type $([[ -n "$namespace" ]] && echo "-n $namespace") \
    $([[ -n "$label_selector" ]] && echo "-l $label_selector") \
    $([[ -n "$field_selector" ]] && echo "--field-selector=$field_selector") \
    -o wide | grep -i "$search_term"
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
    description="Changes the number of replicas for a Kubernetes resource",
    content="""
    #!/bin/bash
    set -e
    kubectl scale $resource_type/$resource_name --replicas=$replicas $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., deployment, statefulset)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

get_resource_events_tool = KubernetesTool(
    name="get_resource_events",
    description="Fetches the last events for a Kubernetes resource",
    content="""
    #!/bin/bash
    set -e
    kubectl describe $resource_type $resource_name $([[ -n "$namespace" ]] && echo "-n $namespace") | tail -n +$(($(kubectl describe $resource_type $resource_name $([[ -n "$namespace" ]] && echo "-n $namespace") | grep -n "Events:" | cut -d ":" -f 1) + 1))
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., pod, deployment)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

get_resource_logs_tool = KubernetesTool(
    name="get_resource_logs",
    description="Fetches logs for a Kubernetes resource",
    content="""
    #!/bin/bash
    set -e
    kubectl logs $resource_type/$resource_name $([[ -n "$namespace" ]] && echo "-n $namespace") $([[ -n "$container" ]] && echo "-c $container") $([[ "$previous" == "true" ]] && echo "-p") $([[ -n "$tail" ]] && echo "--tail=$tail")
    """,
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., pod, deployment)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
        Arg(name="container", type="str", description="Container name (for multi-container pods)", required=False),
        Arg(name="previous", type="bool", description="Fetch logs from previous terminated container", required=False),
        Arg(name="tail", type="int", description="Number of lines to show from the end of the logs", required=False),
    ],
)

# Register all tools
for tool in [scale_deployment_tool, find_resource_tool, change_replicas_tool, get_resource_events_tool, get_resource_logs_tool]:
    tool_registry.register("kubernetes", tool)

# Add any other automation tools here...

cluster_health_tool = KubernetesTool(
    name="cluster_health",
    description="Provides a summary of the Kubernetes cluster health",
    content="""
    #!/bin/bash
    set -e
    echo "Cluster Health Summary:"
    echo "======================="
    echo "Node Status:"
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason
    echo "\nPod Status:"
    kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
    echo "\nDeployment Status:"
    kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,DESIRED:.spec.replicas,AVAILABLE:.status.availableReplicas,UP-TO-DATE:.status.updatedReplicas
    echo "\nPersistent Volume Status:"
    kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name
    """,
    args=[],
)

node_status_tool = KubernetesTool(
    name="node_status",
    description="Lists Kubernetes nodes with their status and emojis",
    content="""
    #!/bin/bash
    set -e
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason | 
    awk 'NR>1 {
        status = $2;
        emoji = "❓";
        if (status == "Ready") emoji = "✅";
        else if (status == "NotReady") emoji = "❌";
        else if (status == "SchedulingDisabled") emoji = "🚫";
        print $1 " " emoji " " $2 " (" $3 ")";
    }'
    """,
    args=[],
)

find_suspicious_errors_tool = KubernetesTool(
    name="find_suspicious_errors",
    description="Finds suspicious errors in a Kubernetes namespace",
    content="""
    #!/bin/bash
    set -e
    namespace="${namespace:-default}"
    echo "Searching for suspicious errors in namespace: $namespace"
    echo "======================================================="
    kubectl get events -n $namespace --sort-by=.metadata.creationTimestamp | 
    grep -E "Error|Failed|CrashLoopBackOff|Evicted|OOMKilled" |
    tail -n 20
    echo "\nPods with non-Running status:"
    kubectl get pods -n $namespace --field-selector status.phase!=Running
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to search for errors", required=False),
    ],
)

resource_usage_tool = KubernetesTool(
    name="resource_usage",
    description="Shows resource usage of nodes or pods",
    content="""
    #!/bin/bash
    set -e
    resource_type="${1:-nodes}"
    namespace="${2:-}"
    if [ "$resource_type" = "nodes" ]; then
        kubectl top nodes
    elif [ "$resource_type" = "pods" ]; then
        kubectl top pods $([[ -n "$namespace" ]] && echo "-n $namespace") --sort-by=cpu
    else
        echo "Invalid resource type. Use 'nodes' or 'pods'."
        exit 1
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Resource type to show usage for (nodes or pods)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (for pods only)", required=False),
    ],
)

check_pod_restarts_tool = KubernetesTool(
    name="check_pod_restarts",
    description="Checks for pods with high restart counts",
    content="""
    #!/bin/bash
    set -e
    namespace="${namespace:-}"
    threshold="${threshold:-5}"
    kubectl get pods $([[ -n "$namespace" ]] && echo "-n $namespace") -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,STATUS:.status.phase |
    awk -v threshold="$threshold" '$3 >= threshold {print $0}'
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
        Arg(name="threshold", type="int", description="Minimum number of restarts to report", required=False),
    ],
)

# Register all tools
for tool in [
    scale_deployment_tool,
    find_resource_tool,
    change_replicas_tool,
    get_resource_events_tool,
    get_resource_logs_tool,
    cluster_health_tool,
    node_status_tool,
    find_suspicious_errors_tool,
    resource_usage_tool,
    check_pod_restarts_tool,
]:
    tool_registry.register("kubernetes", tool)

# Add any other automation tools here...

# New tools

network_policy_analyzer_tool = KubernetesTool(
    name="network_policy_analyzer",
    description="Analyzes network policies in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Network Policy Analysis:"
    echo "========================"
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
    description="Checks Pod Disruption Budgets (PDBs) in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Pod Disruption Budgets:"
    echo "======================="
    kubectl get pdb --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,MIN-AVAILABLE:.spec.minAvailable,MAX-UNAVAILABLE:.spec.maxUnavailable,ALLOWED-DISRUPTIONS:.status.disruptionsAllowed
    """,
    args=[],
)

# Register all tools
for tool in [
    # ... (previous tools)
    network_policy_analyzer_tool,
    persistent_volume_usage_tool,
    ingress_analyzer_tool,
    resource_quota_usage_tool,
    cluster_autoscaler_status_tool,
    pod_disruption_budget_checker_tool,
]:
    tool_registry.register("kubernetes", tool)