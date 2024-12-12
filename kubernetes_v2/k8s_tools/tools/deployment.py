from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

deployment_management_tool = KubernetesTool(
    name="deployment_management",
    description="Creates, deletes, or retrieves information on a Kubernetes deployment.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required for managing a specific deployment."
        exit 1
    fi

    # Set flags for optional parameters
    namespace_flag="-n $namespace"
    image_flag=$( [ "$action" = "create" ] && [ -n "$image" ] && echo "--image=$image" || echo "" )
    replicas_flag=$( [ "$action" = "create" ] && [ -n "$replicas" ] && echo "--replicas=$replicas" || echo "" )

    # Execute the kubectl command
    kubectl $action deployment $name $image_flag $replicas_flag $namespace_flag
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (required for targeting a specific deployment)", required=True),
        Arg(name="image", type="str", description="Container image (for create)", required=False),
        Arg(name="replicas", type="int", description="Number of replicas (for create)", required=False),
    ],
)


scale_deployment_tool = KubernetesTool(
    name="scale_deployment",
    description="Scales a Kubernetes deployment in a specific namespace",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Attempt to scale the deployment
    if kubectl scale deployment "$name" --replicas="$replicas" $namespace_flag; then
        echo "✅ Successfully scaled deployment $name to $replicas replicas in namespace $namespace"
    else
        echo "❌ Failed to scale deployment $name in namespace $namespace"
        exit 1
    fi
    """,
    args=[
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

deployment_rollout_tool = KubernetesTool(
    name="deployment_rollout",
    description="Manages rollouts for a Kubernetes deployment, including status, history, undo, and restart.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required to perform rollout actions on a specific deployment."
        exit 1
    fi

    # Execute the rollout action
    case "$action" in
        status|history|undo|restart)
            kubectl rollout $action deployment $name -n $namespace
            ;;
        *)
            echo "❌ Invalid action for deployment rollout. Use 'status', 'history', 'undo', or 'restart'."
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Rollout action to perform (status, history, undo, restart)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

deployment_describe_tool = KubernetesTool(
    name="deployment_describe",
    description="Describes a Kubernetes deployment, providing detailed configuration and status information.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required to describe a specific deployment."
        exit 1
    fi

    # Describe the deployment
    kubectl describe deployment $name -n $namespace
    """,
    args=[
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace (required for describing a specific deployment)", required=True),
    ],
)

for tool in [
    deployment_management_tool,
    scale_deployment_tool,
    deployment_rollout_tool,
    deployment_describe_tool,
]:
    tool_registry.register("kubernetes", tool)
