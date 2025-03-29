from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_usage_tool = KubernetesTool(
    name="resource_usage",
    description="Shows resource usage of nodes or pods, requiring a namespace or 'all' for all namespaces",
    content="""
    #!/bin/bash
    set -e

    # Ensure resource type is either 'nodes' or 'pods'
    if [ "$resource_type" != "nodes" ] && [ "$resource_type" != "pods" ]; then
        echo "❌ Invalid resource type. Use 'nodes' or 'pods'."
        exit 1
    fi

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Namespace is required. Please specify a namespace or 'all' for all namespaces."
        exit 1
    fi

    # Set namespace flag
    namespace_flag=$( [ "$namespace" = "all" ] && echo "--all-namespaces" || echo "-n $namespace" )

    if [ "$resource_type" = "nodes" ]; then
        echo "🖥️  Node Resource Usage:"
        echo "======================="
        kubectl top nodes | awk 'NR>1 {print "  💻 " $0}'
    elif [ "$resource_type" = "pods" ]; then
        echo "🛠️  Pod Resource Usage:"
        echo "====================="
        kubectl top pods $namespace_flag | awk 'NR>1 {print "  🔧 " $0}'
    fi
    """,
    args=[
        Arg(name="resource_type", type="str", description="Resource type to show usage for (nodes or pods)", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace or 'all' for all namespaces", required=True),
    ],
)



cluster_health_tool = KubernetesTool(
    name="cluster_health",
    description="Provides a summary of the Kubernetes cluster health",
    content="""
    #!/bin/bash
    set -e
    echo "🏥 Cluster Health Summary:"
    echo "========================="
    echo "🖥️  Node Status:"
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason | 
    awk 'NR>1 {
        status = $2;
        emoji = "❓";
        if (status == "Ready") emoji = "✅";
        else if (status == "NotReady") emoji = "❌";
        else if (status == "SchedulingDisabled") emoji = "🚫";
        print "  " emoji " " $0;
    }'
    echo "\n🛠️  Pod Status:"
    kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName | 
    awk 'NR>1 {
        status = $3;
        emoji = "❓";
        if (status == "Running") emoji = "✅";
        else if (status == "Pending") emoji = "⏳";
        else if (status == "Succeeded") emoji = "🎉";
        else if (status == "Failed") emoji = "❌";
        else if (status == "Unknown") emoji = "❔";
        print "  " emoji " " $0;
    }'
    echo "\n🚀 Deployment Status:"
    kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,DESIRED:.spec.replicas,AVAILABLE:.status.availableReplicas,UP-TO-DATE:.status.updatedReplicas | 
    awk 'NR>1 {
        if ($3 == $4 && $3 == $5) emoji = "✅";
        else if ($4 == "0") emoji = "❌";
        else emoji = "⚠️";
        print "  " emoji " " $0;
    }'
    echo "\n💾 Persistent Volume Status:"
    kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name | 
    awk 'NR>1 {
        status = $3;
        emoji = "❓";
        if (status == "Bound") emoji = "✅";
        else if (status == "Available") emoji = "🆓";
        else if (status == "Released") emoji = "🔓";
        else if (status == "Failed") emoji = "❌";
        print "  " emoji " " $0;
    }'
    """,
    args=[],
)

# Register all tools
for tool in [
    resource_usage_tool,
    cluster_health_tool,
]:
    tool_registry.register("kubernetes", tool)
