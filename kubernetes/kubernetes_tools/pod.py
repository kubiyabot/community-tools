from kubiya_sdk.tools import Arg
from .config import COMMON_ENV_VARS, COMMON_FILES

POD_TOOL = {
    "name": "kubernetes_pod",
    "image": "bitnami/kubectl:latest",
    "description": "Manages Kubernetes pods.",
    "alias": "k8s_pod",
    "type": "container",
    "content": "kubectl {{if .kubeconfig}}--kubeconfig={{.kubeconfig}} {{end}}{{.action}} pod {{.name}} {{.args}}",
    "args": [
        Arg(
            name="action",
            type="str",
            description="Action to perform on the pod. Valid options are 'get', 'delete', 'logs'.",
            required=True
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the pod.",
            required=True
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace for the pod.",
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
        "tags": ["Kubernetes", "Pod"],
        "image_url": "https://kubernetes.io/images/favicon.png",
        "documentation": "https://kubernetes.io/docs/concepts/workloads/pods/"
    }
}

async def execute(args: dict) -> dict:
    action = args["action"]
    name = args["name"]
    namespace = args.get("namespace")
    kubeconfig = args.get("kubeconfig", "/root/.kube/config")

    kubectl_args = f"--kubeconfig={kubeconfig} {action} pod {name}"
    
    if namespace:
        kubectl_args += f" --namespace={namespace}"

    full_command = f"kubectl {kubectl_args}"
    
    return {"command": full_command}