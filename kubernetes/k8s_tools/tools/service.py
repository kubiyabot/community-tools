from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

service_tool = KubernetesTool(
    name="service",
    description="Manages Kubernetes services",
    content="""
    #!/bin/bash
    set -e
    kubectl $action service $name \
    $([[ -n "$type" ]] && echo "--type=$type") \
    $([[ -n "$port" ]] && echo "--port=$port") \
    $([[ -n "$target_port" ]] && echo "--target-port=$target_port") \
    $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="type", type="str", description="Type of service (ClusterIP, NodePort, LoadBalancer)", required=False),
        Arg(name="port", type="int", description="Port number", required=False),
        Arg(name="target_port", type="int", description="Target port number", required=False),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

tool_registry.register("kubernetes", service_tool)
