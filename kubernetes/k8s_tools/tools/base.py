# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool
from .common import COMMON_ENVIRONMENT_VARIABLES, COMMON_FILE_SPECS

KUBERNETES_ICON_URL = "https://cdn-icons-png.flaticon.com/256/3889/3889548.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Prepare the script to inject in-cluster context and use the temporary token file
        inject_kubernetes_context = """
#!/bin/bash
set -e

# Inject in-cluster context using the temporary token file
if [ -f /tmp/kubernetes_context_token ]; then
    KUBE_TOKEN=$(cat /tmp/kubernetes_context_token)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster
    kubectl config use-context in-cluster
else
    echo "Error: Kubernetes context token file not found at /tmp/kubernetes_context_token"
    exit 1
fi
"""

        # Strip extra `#!/bin/bash` and remove leading spaces from the caller-provided content
        sanitized_content = content.strip().lstrip("#!/bin/bash").strip()

        # Combine the Kubernetes context setup and the caller's provided shell script
        full_content = f"""{inject_kubernetes_context}
{sanitized_content}
"""

        # Initialize the Tool superclass with the combined content and other parameters
        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=COMMON_ENVIRONMENT_VARIABLES,
            with_files=COMMON_FILE_SPECS,
        )
