from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

deployment_tool = KubernetesTool(
    name="deployment_management",
    description="Manages Kubernetes deployments with proper output truncation",
    content='''
    #!/bin/bash
    set -e

    # Ensure required parameters are provided
    if [ -z "${namespace}" ] || [ -z "${name}" ] || [ -z "${action}" ]; then
        echo "❌ Error: namespace, name, and action are required."
        exit 1
    fi

    # Build base command
    base_cmd="kubectl --namespace ${namespace}"

    case "${action}" in
        create|update)
            if [ -z "${image}" ]; then
                echo "❌ Error: image is required for create/update actions"
                exit 1
            fi
            replicas=${replicas:-1}
            
            # Build create/update command
            cmd="${base_cmd} create deployment ${name} --image=${image} --replicas=${replicas} --dry-run=client -o yaml"
            if ! eval "$cmd" | kubectl apply -f -; then
                echo "❌ Failed to ${action} deployment ${name}"
                exit 1
            fi
            echo "✅ Successfully ${action}d deployment ${name}"
            
            # Show deployment status with truncation
            status_cmd="${base_cmd} get deployment ${name}"
            show_resource_status "$status_cmd" "Deployment" "$name"
            
            # Show associated pods
            echo -e "\n📦 Associated Pods:"
            echo "=================="
            pods_cmd="${base_cmd} get pods -l app=${name}"
            kubectl_with_truncation "$pods_cmd"
            
            # Show events
            format_events "$namespace" "$name" "Deployment"
            ;;
            
        delete)
            cmd="${base_cmd} delete deployment ${name}"
            if ! eval "$cmd"; then
                echo "❌ Failed to delete deployment ${name}"
                exit 1
            fi
            echo "✅ Successfully deleted deployment ${name}"
            ;;
            
        get)
            # Show deployment details
            cmd="${base_cmd} get deployment ${name}"
            show_resource_status "$cmd" "Deployment" "$name"
            
            # Show associated pods
            echo -e "\n📦 Associated Pods:"
            echo "=================="
            pods_cmd="${base_cmd} get pods -l app=${name}"
            kubectl_with_truncation "$pods_cmd"
            
            # Show events
            format_events "$namespace" "$name" "Deployment"
            ;;
            
        *)
            echo "❌ Error: Invalid action. Supported actions are create, update, delete, get"
            exit 1
            ;;
    esac
    ''',
    args=[
        Arg(name="action", type="str", description="Action to perform (create, update, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="image", type="str", description="Container image (for create/update)", required=False),
        Arg(name="replicas", type="int", description="Number of replicas (for create/update)", required=False),
    ],
)


scale_deployment_tool = KubernetesTool(
    name="scale_deployment",
    description="Scales a Kubernetes deployment in a specific namespace",
    content='''
    #!/bin/bash
    set -e

    # Check if namespace is provided
    if [ -z "${namespace}" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n ${namespace}"

    # Attempt to scale the deployment
    if ! kubectl scale deployment "${name}" --replicas="${replicas}" ${namespace_flag}; then
        echo "❌ Failed to scale deployment ${name} in namespace ${namespace}"
        exit 1
    fi

    echo "✅ Successfully scaled deployment ${name} to ${replicas} replicas in namespace ${namespace}"
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

deployment_rollout_tool = KubernetesTool(
    name="deployment_rollout",
    description="Manages rollouts for a Kubernetes deployment, including status, history, undo, and restart.",
    content='''
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "${namespace}" ]; then
        echo "❌ Error: Namespace is required to perform rollout actions on a specific deployment."
        exit 1
    fi

    # Execute the rollout action
    case "${action}" in
        status|history|undo|restart)
            if ! kubectl rollout "${action}" deployment "${name}" -n "${namespace}"; then
                echo "❌ Failed to perform rollout ${action} on deployment ${name} in namespace ${namespace}"
                exit 1
            fi
            ;;
        *)
            echo "❌ Invalid action for deployment rollout. Use 'status', 'history', 'undo', or 'restart'."
            exit 1
            ;;
    esac

    echo "✅ Successfully performed rollout ${action} on deployment ${name} in namespace ${namespace}"
    ''',
    args=[
        Arg(name="action", type="str", description="Rollout action to perform (status, history, undo, restart)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

deployment_describe_tool = KubernetesTool(
    name="deployment_describe",
    description="Describes a Kubernetes deployment, providing detailed configuration and status information.",
    content='''
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "${namespace}" ]; then
        echo "❌ Error: Namespace is required to describe a specific deployment."
        exit 1
    fi

    # Describe the deployment
    if ! kubectl describe deployment "${name}" -n "${namespace}"; then
        echo "❌ Failed to describe deployment ${name} in namespace ${namespace}"
        exit 1
    fi
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

for tool in [
    deployment_tool,
    scale_deployment_tool,
    deployment_rollout_tool,
    deployment_describe_tool,
]:
    tool_registry.register("kubernetes", tool)
