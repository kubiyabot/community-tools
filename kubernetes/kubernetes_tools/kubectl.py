from kubiya_sdk.tools import Arg
from .config import COMMON_ENV_VARS, COMMON_FILES

KUBECTL_TOOL = {
    "name": "kubectl",
    "image": "bitnami/kubectl:latest",
    "description": "Executes kubectl commands to interact with Kubernetes clusters.",
    "alias": "kubectl",
    "type": "container",
    "content": "kubectl {{if .kubeconfig}}--kubeconfig={{.kubeconfig}} {{end}}{{.command}}",
    "args": [
        Arg(
            name="command",
            type="str",
            description="The kubectl command to execute. For example, 'get pods', 'apply -f /tmp/resource.yaml', or 'delete service myservice'.",
            required=True
        ),
        Arg(
            name="namespace",
            type="str",
            description="The Kubernetes namespace to target. If not specified, uses the current context's namespace or 'default'.",
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
        "tags": ["Kubernetes", "CLI", "Cluster Management"],
        "image_url": "https://kubernetes.io/images/favicon.png",
        "documentation": "https://kubernetes.io/docs/reference/kubectl/overview/"
    }
}

async def execute(args: dict) -> dict:
    command = args["command"]
    namespace = args.get("namespace")
    kubeconfig = args.get("kubeconfig", "/root/.kube/config")
    
    full_command = f"kubectl --kubeconfig={kubeconfig}"
    
    if namespace:
        full_command += f" --namespace={namespace}"
    
    full_command += f" {command}"
    
    return {"command": full_command}