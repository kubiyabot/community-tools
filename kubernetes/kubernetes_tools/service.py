from kubiya_sdk.tools import Arg
from .config import COMMON_ENV_VARS, COMMON_FILES

SERVICE_TOOL = {
    "name": "kubernetes_service",
    "image": "bitnami/kubectl:latest",
    "description": "Manages Kubernetes services.",
    "alias": "k8s_service",
    "type": "container",
    "content": "kubectl {{if .kubeconfig}}--kubeconfig={{.kubeconfig}} {{end}}{{.action}} service {{.name}} {{.args}}",
    "args": [
        Arg(
            name="action",
            type="str",
            description="Action to perform on the service. Valid options are 'create', 'delete', 'get'.",
            required=True
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the service.",
            required=True
        ),
        Arg(
            name="type",
            type="str",
            description="Type of the service (ClusterIP, NodePort, LoadBalancer).",
            required=False
        ),
        Arg(
            name="port",
            type="int",
            description="Port number for the service.",
            required=False
        ),
        Arg(
            name="target_port",
            type="int",
            description="Target port number for the service.",
            required=False
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace for the service.",
            required=False
        ),
        Arg(
            name="kubeconfig",
            type="str",
            description="Path to the kubeconfig file inside the container. If not provided, in-cluster configuration will be used.",
            required=False,
            default="/root/.kube/config"
        ),
    ],
    "env": COMMON_ENV_VARS,
    "files": COMMON_FILES,
    "metadata": {
        "category": ["Kubernetes"],
        "tags": ["Kubernetes", "Service"],
        "image_url": "https://kubernetes.io/images/favicon.png",
        "documentation": "https://kubernetes.io/docs/concepts/services-networking/service/"
    }
}

async def execute(args: dict) -> dict:
    action = args["action"]
    name = args["name"]
    service_type = args.get("type")
    port = args.get("port")
    target_port = args.get("target_port")
    namespace = args.get("namespace")
    kubeconfig = args.get("kubeconfig", "/root/.kube/config")

    kubectl_args = f"--kubeconfig={kubeconfig} {action} service {name}"
    
    if action == "create":
        if service_type:
            kubectl_args += f" --type={service_type}"
        if port:
            kubectl_args += f" --port={port}"
        if target_port:
            kubectl_args += f" --target-port={target_port}"
    
    if namespace:
        kubectl_args += f" --namespace={namespace}"

    full_command = f"kubectl {kubectl_args}"
    
    return {"command": full_command}