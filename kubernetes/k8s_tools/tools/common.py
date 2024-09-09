# k8s_tools/tools/common.py

from kubiya_sdk.tools import FileSpec

COMMON_ENV = [
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_SERVICE_PORT",
]

COMMON_FILES = [
    FileSpec(
        source="/var/run/secrets/kubernetes.io/serviceaccount/token",
        destination="/tmp/kubernetes_context_token"
    ),
]
