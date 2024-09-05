from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

pod_tool = KubernetesTool(
    name="pod",
    description="Manages Kubernetes pods",
    content="""
    #!/bin/bash
    set -e
    if [[ "$action" == "logs" ]]; then
        kubectl logs $name $([[ -n "$container" ]] && echo "-c $container") $([[ -n "$namespace" ]] && echo "-n $namespace")
    else
        kubectl $action pod $name $([[ -n "$namespace" ]] && echo "-n $namespace")
    fi
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (get, delete, logs)", required=True),
        Arg(name="name", type="str", description="Name of the pod", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
        Arg(name="container", type="str", description="Container name (for logs)", required=False),
    ],
)

tool_registry.register("kubernetes", pod_tool)
