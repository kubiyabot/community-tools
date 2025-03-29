from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes kubectl commands. For namespace-scoped resources, include '-n <namespace>' in the command. Use '--all-namespaces' for cluster-wide queries. Some resources like nodes and persistent volumes are cluster-scoped and don't require a namespace.",
    content="""
    #!/bin/bash
    set -e

    # Show the command being executed
    echo "🔧 Executing: kubectl $command"

    # Run the kubectl command
    if eval "kubectl $command"; then
        echo "✅ Command executed successfully"
    else
        echo "❌ Command failed: kubectl $command"
        exit 1
    fi
    """,
    args=[
        Arg(
            name="command", 
            type="str", 
            description="The full kubectl command to execute. Examples include (but are not limited to):\n" +
                       "- 'get pods -n default'\n" +
                       "- 'create namespace test'\n" +
                       "- 'get pods --all-namespaces'\n" +
                       "- 'get nodes'  # cluster-scoped resource, no namespace needed\n" +
                       "- 'describe node my-node-1'",
            required=True
        ),
    ],
)

tool_registry.register("kubernetes", kubectl_tool)
