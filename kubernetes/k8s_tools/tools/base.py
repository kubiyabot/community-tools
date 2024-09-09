# k8s_tools/tools/base.py

from kubiya_sdk.tools import Tool
from .common import COMMON_ENV, COMMON_FILES

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Prepare the content to inject in-cluster context
        in_cluster_setup = """
        # Inject in-cluster context
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
        
        # Combine the in-cluster setup with the original content
        full_content = in_cluster_setup + "\n" + content

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
        )
