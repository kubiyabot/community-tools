from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes kubectl commands",
    content="""
    #!/bin/bash
    set -e
    kubectl $command $([[ -n "$namespace" ]] && echo "-n $namespace")
    """,
    args=[
        Arg(name="command", type="str", description="The kubectl command to execute", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
)

tool_registry.register("kubernetes", kubectl_tool)
