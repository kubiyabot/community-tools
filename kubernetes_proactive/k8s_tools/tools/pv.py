from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

pv_management_tool = KubernetesTool(
    name="pv_management", 
    description="Creates, deletes, or retrieves information on a Kubernetes persistent volume.",
    content="""
    #!/bin/bash
    set -e

    # Set flags for optional parameters
    size_flag=$( [ "$action" = "create" ] && [ -n "$size" ] && echo "--size=$size" || echo "" )
    storage_class_flag=$( [ "$action" = "create" ] && [ -n "$storage_class" ] && echo "--storage-class=$storage_class" || echo "" )
    access_mode_flag=$( [ "$action" = "create" ] && [ -n "$access_mode" ] && echo "--access-mode=$access_mode" || echo "" )

    # Execute the kubectl command
    case "$action" in
        create)
            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: $name
spec:
  capacity:
    storage: ${size:-1Gi}
  accessModes:
    - ${access_mode:-ReadWriteOnce}
  storageClassName: ${storage_class:-standard}
  hostPath:
    path: /data/$name
EOF
            ;;
        delete)
            kubectl delete pv "$name"
            ;;
        get)
            kubectl get pv "$name" -o yaml
            ;;
        *)
            echo "❌ Invalid action. Supported actions are create, delete, get"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the persistent volume", required=True),
        Arg(name="size", type="str", description="Size of the volume (e.g. 1Gi)", required=False),
        Arg(name="storage_class", type="str", description="Storage class name", required=False),
        Arg(name="access_mode", type="str", description="Access mode (ReadWriteOnce, ReadOnlyMany, ReadWriteMany)", required=False),
    ],
)

pv_describe_tool = KubernetesTool(
    name="pv_describe",
    description="Describes a Kubernetes persistent volume, providing detailed configuration and status information.",
    content="""
    #!/bin/bash
    set -e

    # Describe the persistent volume
    kubectl describe pv $name
    """,
    args=[
        Arg(name="name", type="str", description="Name of the persistent volume", required=True),
    ],
)

pv_list_tool = KubernetesTool(
    name="pv_list",
    description="Lists all persistent volumes in the cluster with optional filtering.",
    content="""
    #!/bin/bash
    set -e

    # Build command with optional filters
    cmd="kubectl get pv"
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
        Arg(name="storage_class", type="str", description="Filter by storage class", required=False),
        Arg(name="status", type="str", description="Filter by status (Bound, Available, Released)", required=False),
    ],
)

for tool in [
    pv_management_tool,
    pv_describe_tool,
    pv_list_tool,
]:
    tool_registry.register("kubernetes", tool)
