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
            description="Precise OpenShift CLI command to execute. Keep it focused and specific. Examples:\\n" +
                       "- 'get pod my-pod-name -n my-project'        # target specific pod in project\\n" +
                       "- 'get pods -n default | grep my-app'        # filter pods by name in project\\n" +
                       "- 'get pods -l app=my-app -n prod'           # use labels for precise filtering\\n" +
                       "- 'get nodes --selector=node-role=worker'    # target specific node types\\n" +
                       "- 'get projects'                             # list all projects\\n" +
                       "- 'get routes -n my-project'                 # get routes in specific project\\n" +
                       "- 'get deploymentconfigs -n my-project'     # get deployment configs\\n" +
                       "- 'get builds -n my-project'                 # get builds in project\\n" +
                       "- 'get imagestreams -n my-project'          # get image streams\\n" +
                       "- 'get services -n my-project'              # get services in project\\n" +
                       "- 'logs deployment/my-app -n my-project'    # get logs from deployment\\n" +
                       "- 'status -n my-project'                    # get project status\\n" +
                       "- 'describe pod my-pod -n my-project'       # describe specific resource\\n\\n" +
                       "Try to use grep to filter output and more specific selectors for better results.",
            required=True
        ),
    ],
)

try:
    tool_registry.register("openshift", oc_tool)
except Exception as e:
    print(f"❌ Failed to register oc tool: {str(e)}", file=sys.stderr)
    raise