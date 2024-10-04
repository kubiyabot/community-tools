# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool
from .common import COMMON_ENVIRONMENT_VARIABLES, COMMON_FILE_SPECS

KUBERNETES_ICON_URL = "https://cdn-icons-png.flaticon.com/256/3889/3889548.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Prepare the script to inject in-cluster context
        inject_kubernetes_context = """
#!/bin/bash
set -e

# Function to check if a file exists and is readable
file_exists_and_readable() {
    [ -f "$1" ] && [ -r "$1" ]
}

# Check for in-cluster configuration
if file_exists_and_readable "/var/run/secrets/kubernetes.io/serviceaccount/token" && \
   file_exists_and_readable "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"; then
    echo "Using in-cluster configuration"
    KUBE_TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster
    kubectl config use-context in-cluster
else
    echo "Error: In-cluster configuration not found"
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
