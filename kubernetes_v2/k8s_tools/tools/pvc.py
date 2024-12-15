from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

pvc_management_tool = KubernetesTool(
    name="pvc_management", 
    description="Creates, deletes, or retrieves information on a Kubernetes persistent volume claim.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required for managing PVCs."
        exit 1
    fi

    # Set flags for optional parameters
    size_flag=$( [ "$action" = "create" ] && [ -n "$size" ] && echo "--size=$size" || echo "" )
    storage_class_flag=$( [ "$action" = "create" ] && [ -n "$storage_class" ] && echo "--storage-class=$storage_class" || echo "" )
    access_mode_flag=$( [ "$action" = "create" ] && [ -n "$access_mode" ] && echo "--access-mode=$access_mode" || echo "" )

    # Execute the kubectl command
    case "$action" in
        create)
            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $name
  namespace: $namespace
spec:
  accessModes:
    - ${access_mode:-ReadWriteOnce}
  resources:
    requests:
      storage: ${size:-1Gi}
  storageClassName: ${storage_class:-standard}
EOF
            ;;
        delete)
            kubectl delete pvc "$name" -n "$namespace"
            ;;
        get)
            kubectl get pvc "$name" -n "$namespace" -o yaml
            ;;
        *)
            echo "❌ Invalid action. Supported actions are create, delete, get"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the persistent volume claim", required=True),
        Arg(name="namespace", type="str", description="Namespace for the PVC", required=True),
        Arg(name="size", type="str", description="Size of the volume claim (e.g. 1Gi)", required=False),
        Arg(name="storage_class", type="str", description="Storage class name", required=False),
        Arg(name="access_mode", type="str", description="Access mode (ReadWriteOnce, ReadOnlyMany, ReadWriteMany)", required=False),
    ],
)

pvc_describe_tool = KubernetesTool(
    name="pvc_describe",
    description="Describes a Kubernetes persistent volume claim, providing detailed configuration and status information.",
    content="""
    #!/bin/bash
    set -e

    # Ensure namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required for describing PVCs."
        exit 1
    fi

    # Describe the persistent volume claim
    kubectl describe pvc "$name" -n "$namespace"
    """,
    args=[
        Arg(name="name", type="str", description="Name of the persistent volume claim", required=True),
        Arg(name="namespace", type="str", description="Namespace of the PVC", required=True),
    ],
)

pvc_list_tool = KubernetesTool(
    name="pvc_list",
    description="Lists persistent volume claims in a namespace with optional filtering.",
    content="""
    #!/bin/bash
    set -e

    # Build command with namespace
    cmd="kubectl get pvc"
    
    if [ -n "${namespace:-}" ]; then
        cmd="$cmd -n $namespace"
    else
        cmd="$cmd --all-namespaces"
    fi

    if [ -n "${storage_class:-}" ]; then
        cmd="$cmd --selector=storageClassName=$storage_class"
    fi
    if [ -n "${status:-}" ]; then
        cmd="$cmd --selector=status.phase=$status"
    fi

    # Execute command
    eval "$cmd"
    """,
    args=[
        Arg(name="namespace", type="str", description="Namespace to list PVCs from (omit for all namespaces)", required=False),
        Arg(name="storage_class", type="str", description="Filter by storage class", required=False),
        Arg(name="status", type="str", description="Filter by status (Bound, Pending)", required=False),
    ],
)

for tool in [
    pvc_management_tool,
    pvc_describe_tool,
    pvc_list_tool,
]:
    tool_registry.register("kubernetes", tool)
