from kubiya_sdk.tools import Arg
from .base import OpenShiftTool
from kubiya_sdk.tools.registry import tool_registry
import sys

oc_tool = OpenShiftTool(
    name="oc",
    description="Executes focused OpenShift CLI (oc) commands with automatic in-cluster context handling. Keep commands simple and precise. For targeted searches, you can use grep (e.g., 'get pods | grep app-name'). Specify project/namespace with '-n namespace' for better targeting. Use '--all-namespaces' only when necessary.",
    content="""
    #!/bin/bash
    set -e

    # Show the command being executed
    echo "🔧 Executing: oc $command"

    # Run the oc command and ensure output is displayed
    output=$(oc $command)
    if [ $? -eq 0 ]; then
        echo "$output" | head -n 100
        echo "-- > For more focused results, consider refining your command or using more specific selectors"
    else
        echo "❌ Command failed: oc $command"
        exit 1
    fi
    """,
    args=[
        Arg(
            name="command", 
            type="str", 
            description="OpenShift CLI command to execute (without 'oc' prefix). Examples: 'get projects', 'get pods -n myproject', 'get routes -n myproject', 'logs deployment/myapp -n myproject', 'status -n myproject'. Use grep and selectors for focused results.",
            required=True
        ),
    ],
)

try:
    tool_registry.register("openshift", oc_tool)
except Exception as e:
    print(f"❌ Failed to register oc tool: {str(e)}", file=sys.stderr)
    raise