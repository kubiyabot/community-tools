from kubiya_sdk.tools import Arg, FileSpec
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

service_management_tool = KubernetesTool(
    name="service_management",
    description="Creates, deletes, or retrieves information on a Kubernetes service.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required to manage a specific service."
        exit 1
    fi

    # Define flags for service creation
    namespace_flag="-n $namespace"
    type_flag=$( [ "$action" = "create" ] && [ -n "$type" ] && echo "--type=$type" || echo "" )
    port_flag=$( [ "$action" = "create" ] && [ -n "$port" ] && echo "--port=$port" || echo "" )
    target_port_flag=$( [ "$action" = "create" ] && [ -n "$target_port" ] && echo "--target-port=$target_port" || echo "" )

    # Execute the kubectl command
    kubectl $action service $name $type_flag $port_flag $target_port_flag $namespace_flag
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (required for managing a specific service)", required=True),
        Arg(name="type", type="str", description="Type of service (ClusterIP, NodePort, LoadBalancer) - only for create action", required=False),
        Arg(name="port", type="int", description="Port number - only for create action", required=False),
        Arg(name="target_port", type="int", description="Target port number - only for create action", required=False),
    ],
    file_specs=[
        FileSpec(...)
    ]
)

# Service Describe Tool
service_describe_tool = KubernetesTool(
    name="service_describe",
    description="Describes a Kubernetes service, providing detailed configuration and status information.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required to describe a specific service."
        exit 1
    fi

    # Describe the service
    kubectl describe service $name -n $namespace
    """,
    args=[
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (required for describing a specific service)", required=True),
    ],
    file_specs=[
        FileSpec(...)
    ]
)

# Register Tools
for tool in [
    service_management_tool,
    service_describe_tool,
]:
    tool_registry.register("kubernetes", tool)
