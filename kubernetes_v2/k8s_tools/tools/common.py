# k8s_tools/tools/common.py
from kubiya_sdk.tools import FileSpec

# Common environment variables for Kubernetes in-cluster context
COMMON_ENVIRONMENT_VARIABLES = []

# Common file specifications for Kubernetes in-cluster authentication
COMMON_FILE_SPECS = [
    FileSpec(
        source="/var/run/secrets/kubernetes.io/serviceaccount/token",
        destination="/tmp/k8s_token",
        description="Kubernetes service account token for in-cluster authentication."
    ),
    FileSpec(
        source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
        destination="/tmp/k8s_ca.crt",
        description="Kubernetes CA certificate for in-cluster authentication."
    ),
]
