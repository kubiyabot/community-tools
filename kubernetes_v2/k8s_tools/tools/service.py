from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

service_tool = KubernetesTool(
    name="service_management",
    description="Manages Kubernetes services with proper output truncation",
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
        create)
            if [ -z "${port}" ]; then
                echo "❌ Error: port is required for create action"
                exit 1
            fi
            
            type=${type:-ClusterIP}
            target_port=${target_port:-$port}
            
            # Build create command
            cmd="${base_cmd} create service ${type} ${name} --tcp=${port}:${target_port} --dry-run=client -o yaml"
            if ! eval "$cmd" | kubectl apply -f -; then
                echo "❌ Failed to create service ${name}"
                exit 1
            fi
            echo "✅ Successfully created service ${name}"
            
            # Show service status with truncation
            status_cmd="${base_cmd} get service ${name}"
            show_resource_status "$status_cmd" "Service" "$name"
            
            # Show endpoints
            echo -e "\n🔌 Service Endpoints:"
            echo "=================="
            endpoints_cmd="${base_cmd} get endpoints ${name}"
            kubectl_with_truncation "$endpoints_cmd"
            
            # Show events
            format_events "$namespace" "$name" "Service"
            ;;
            
        delete)
            cmd="${base_cmd} delete service ${name}"
            if ! eval "$cmd"; then
                echo "❌ Failed to delete service ${name}"
                exit 1
            fi
            echo "✅ Successfully deleted service ${name}"
            ;;
            
        get)
            # Show service details
            cmd="${base_cmd} get service ${name}"
            show_resource_status "$cmd" "Service" "$name"
            
            # Show endpoints
            echo -e "\n🔌 Service Endpoints:"
            echo "=================="
            endpoints_cmd="${base_cmd} get endpoints ${name}"
            kubectl_with_truncation "$endpoints_cmd"
            
            # Show events
            format_events "$namespace" "$name" "Service"
            ;;
            
        *)
            echo "❌ Error: Invalid action. Supported actions are create, delete, get"
            exit 1
            ;;
    esac
    ''',
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="type", type="str", description="Service type (ClusterIP, NodePort, LoadBalancer)", required=False),
        Arg(name="port", type="int", description="Service port", required=False),
        Arg(name="target_port", type="int", description="Target port (defaults to port)", required=False),
    ],
)

# Register tools
tool_registry.register("kubernetes", service_tool)
