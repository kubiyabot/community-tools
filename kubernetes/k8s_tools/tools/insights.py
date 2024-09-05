from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_usage_tool = KubernetesTool(
    name="resource_usage",
    description="Gathers resource usage insights for the cluster",
    content="""
    #!/bin/bash
    set -e
    kubectl top nodes
    kubectl top pods $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

cluster_health_tool = KubernetesTool(
    name="cluster_health",
    description="Checks overall cluster health",
    content="""
    #!/bin/bash
    set -e
    kubectl get nodes
    kubectl get pods --all-namespaces
    kubectl get events --all-namespaces
    """,
    args=[],
)

tool_registry.register("kubernetes", resource_usage_tool)
tool_registry.register("kubernetes", cluster_health_tool)
