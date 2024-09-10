# k8s_tools/tools/common.py

from kubiya_sdk.tools import FileSpec

COMMON_ENV = [
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_SERVICE_PORT",
]

COMMON_FILES = [
    FileSpec(
        # This is the token that will be used to authenticate with Kubernetes
        # It is mounted into the container at /var/run/secrets/kubernetes.io/serviceaccount/token
        # We need to copy it to a temporary file that the script can use to set the context
        # CAN BE USED ONLY FROM WITHIN A KUBERNETES CLUSTER (eg. in a pod)
        # TODO:: Figure a way to dynamically use kubeconfig
        source="/var/run/secrets/kubernetes.io/serviceaccount/token",
        destination="/tmp/kubernetes_context_token"
    ),
]
