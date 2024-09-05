from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

deployment_tool = KubernetesTool(
    name="deployment",
    description="Manages Kubernetes deployments",
    content="""
    #!/bin/bash
    set -e
    kubectl $action deployment $name \
    $([[ -n "$image" ]] && echo "--image=$image") \
    $([[ -n "$replicas" ]] && echo "--replicas=$replicas") \
    $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, update, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="image", type="str", description="Container image for create/update actions", required=False),
        Arg(name="replicas", type="int", description="Number of replicas", required=False),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

tool_registry.register("kubernetes", deployment_tool)
