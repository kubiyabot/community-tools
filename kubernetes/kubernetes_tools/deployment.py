from kubiya_sdk.tools import Arg
from .config import COMMON_ENV_VARS, COMMON_FILES

DEPLOYMENT_TOOL = {
    "name": "kubernetes_deployment",
    "image": "bitnami/kubectl:latest",
    "description": "Manages Kubernetes deployments.",
    "alias": "k8s_deployment",
    "type": "container",
    "content": "kubectl {{if .kubeconfig}}--kubeconfig={{.kubeconfig}} {{end}}{{.action}} deployment {{.name}} {{.args}}",
    "args": [
        Arg(
            name="action",
            type="str",
            description="Action to perform on the deployment. Valid options are 'create', 'update', 'delete', 'get', 'scale'.",
            required=True
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the deployment.",
            required=True
        ),
        Arg(
            name="image",
            type="str",
            description="Container image for the deployment (required for 'create' and 'update' actions).",
            required=False
        ),
        Arg(
            name="replicas",
            type="int",
            description="Number of replicas for the deployment.",
            required=False
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace for the deployment.",
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
        "tags": ["Kubernetes", "Deployment"],
        "image_url": "https://kubernetes.io/images/favicon.png",
        "documentation": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/"
    }
}

async def execute(args: dict) -> dict:
    action = args["action"]
    name = args["name"]
    image = args.get("image")
    replicas = args.get("replicas")
    namespace = args.get("namespace")
    kubeconfig = args.get("kubeconfig", "/root/.kube/config")

    kubectl_args = f"--kubeconfig={kubeconfig} {action} deployment {name}"
    
    if action in ["create", "update"]:
        if not image:
            raise ValueError("Image is required for create and update actions")
        kubectl_args += f" --image={image}"
    
    if replicas is not None:
        kubectl_args += f" --replicas={replicas}"
    
    if namespace:
        kubectl_args += f" --namespace={namespace}"

    full_command = f"kubectl {kubectl_args}"
    
    return {"command": full_command}