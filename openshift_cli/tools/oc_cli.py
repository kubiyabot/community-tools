from kubiya_sdk.tools.models import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import BaseOCTool

oc_cli_tool = BaseOCTool(
    name="oc_cli",
    description="Executes OpenShift CLI (oc) commands. For namespace/project-scoped resources, include '-n <namespace>' in the command. Some resources like nodes and cluster settings are cluster-scoped and don't require a namespace/project.",
    content="""
    #!/bin/bash
    set -e

    # Show the command being executed
    echo "🔧 Executing: oc $command"

    # Run the OpenShift command
    if eval "oc $command"; then
        echo "✅ Command executed successfully"
    else
        echo "❌ Command failed: oc $command"
        exit 1
    fi
    """,
    args=[
        Arg(
            name="command", 
            type="str", 
            description="The full OpenShift CLI command to execute. Examples include (but are not limited to):\n" +
                       "- 'get pods -n default'\n" +
                       "- 'new-project my-project'\n" +
                       "- 'get projects'\n" +
                       "- 'get nodes'  # cluster-scoped resource, no namespace needed\n" +
                       "- 'get routes -n my-project'\n" +
                       "- 'adm policy add-cluster-role-to-user cluster-admin username'",
            required=True
        ),
    ],
)

# Register the tool
tool_registry.register("openshift", oc_cli_tool) 