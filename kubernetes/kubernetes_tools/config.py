from kubiya_sdk.tools import Source

KUBERNETES_TOOLS_SOURCE = Source(value="https://github.com/example/kubernetes-tools-module")

COMMON_ENV_VARS = [
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_SERVICE_PORT",
]

COMMON_FILES = [
    {
        "source": "~/.kube/config",
        "destination": "/root/.kube/config"
    }
]