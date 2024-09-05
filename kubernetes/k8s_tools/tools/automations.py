from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

scale_deployment_tool = KubernetesTool(
    name="scale_deployment",
    description="Scales a deployment to a specified number of replicas",
    content="""
    #!/bin/bash
    set -e
    kubectl scale deployment $deployment --replicas=$replicas $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="deployment", type="str", description="Name of the deployment", required=True),
        Arg(name="replicas", type="int", description="Number of desired replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

tool_registry.register("kubernetes", scale_deployment_tool)
