# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

KUBERNETES_ICON_URL = "https://kubernetes.io/icons/icon-128x128.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        inject_kubernetes_context = """
set -eu
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"
# Inject in-cluster context using the temporary token file
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                          --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "Error: Kubernetes context token or cert file not found at $TOKEN_LOCATION \
          or $CERT_LOCATION respectively."
    exit 1
fi
"""
        full_content = f"{inject_kubernetes_context}\n{content}"

        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            with_files=file_specs,
        )

# Example usage:
kubectl_cli = KubernetesTool(
    name="kubectl_cli",
    description="Runs any Kubernetes commands using the `kubectl` binary.",
    content="kubectl {{.command}}",
    args=[
        Arg(
            name="command",
            description="The Kubernetes CLI command to run. Do not use `kubectl`, only enter its command.",
            required=True
        )
    ]
)
