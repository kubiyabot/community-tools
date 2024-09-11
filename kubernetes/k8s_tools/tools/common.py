# k8s_tools/tools/common.py
from kubiya_sdk.tools import FileSpec

# Common environment variables for Kubernetes in-cluster context
COMMON_ENVIRONMENT_VARIABLES = [
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_SERVICE_PORT",
]

# Common file specifications, including the Kubernetes service account token
COMMON_FILE_SPECS = [
    FileSpec(
        # Copy the service account token to a temporary location for use in the container
        source="/var/run/secrets/kubernetes.io/serviceaccount/token",
        destination="/tmp/kubernetes_context_token",
       # description="Kubernetes service account token for in-cluster authentication."
    ),
]
