from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry
import sys

kubectl_tool = KubernetesTool(
    name="kubectl",
    description="Executes focused kubectl commands. Keep commands simple and precise. For targeted searches, you can use grep (e.g., 'get pods | grep app-name'). Specify namespace with '-n namespace' for better targeting. Use '--all-namespaces' only when necessary.",
    content="""
    #!/bin/bash
    set -e

    # Show the command being executed
    echo "🔧 Executing: kubectl $command"

    # Run the kubectl command with limited output (100 lines max)
    # Using a subshell to capture the real exit status while still limiting output
    if (kubectl $command | head -n 100); then
        echo "✅ Command executed successfully"
        echo "Note: Output limited to 100 lines. For more focused results, consider using grep or more specific selectors."
    else
        echo "❌ Command failed: kubectl $command"
        exit 1
    fi
    """,
    args=[
        Arg(
            name="command", 
            type="str", 
            description="Precise kubectl command to execute. Keep it focused and specific. Examples:\n" +
                       "- 'get pod my-pod-name -n my-namespace'  # target specific pod\n" +
                       "- 'get pods -n default | grep my-app'    # filter pods by name\n" +
                       "- 'get pods -l app=my-app -n prod'       # use labels for precise filtering\n" +
                       "- 'get nodes --selector=node-role=worker' # target specific node types",
            required=True
        ),
    ],
)

try:
    tool_registry.register("kubernetes", kubectl_tool)
except Exception as e:
    print(f"❌ Failed to register kubectl tool: {str(e)}", file=sys.stderr)
    raise
