from typing import Optional
from kubiya_sdk.tools.models import Arg, Tool
from pydantic import HttpUrl
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry

TRIVY_LOGO = HttpUrl(
    "https://raw.githubusercontent.com/aquasecurity/trivy/main/docs/imgs/logo.png"
)

COMMON_ENVS = [
    "OPENSHIFT_URL",
    "OPENSHIFT_USERNAME",
]

COMMON_SECRETS = [
    "OPENSHIFT_PASSWORD",
]

class TrivyTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list[Arg] = [],
        env: list[str] = [],
        secrets: list[str] = [],
        long_running=False,
    ):
        # Add common environment variables and secrets
        for common_env in COMMON_ENVS:
            if common_env not in env:
                env.append(common_env)
        for common_secret in COMMON_SECRETS:
            if common_secret not in secrets:
                secrets.append(common_secret)
        
        # Wrap content with OpenShift login and Trivy setup
        content = f"""
set -e

# Login to OpenShift and get the kubeconfig
if ! oc login "$OPENSHIFT_URL" \\
    --username="$OPENSHIFT_USERNAME" \\
    --password="$OPENSHIFT_PASSWORD" \\
    --insecure-skip-tls-verify=true; then
    echo "Failed to login to OpenShift cluster"
    exit 1
fi

# Save kubeconfig and set up registry auth
mkdir -p /tmp/.kube
oc config view --minify > /tmp/.kube/config
export KUBECONFIG=/tmp/.kube/config

# Get registry credentials for internal registry
mkdir -p /tmp/auth
REGISTRY_AUTH_FILE=/tmp/auth/config.json
oc registry login --to=$REGISTRY_AUTH_FILE
export DOCKER_CONFIG=/tmp/auth

# Configure Trivy to use k8s mode and skip container runtime
export TRIVY_INSECURE=true
export TRIVY_K8S_USECRI=false
export TRIVY_NON_SSL=true
export TRIVY_TIMEOUT=10m
export TRIVY_SKIP_POLICY="quay.io/openshift-release-dev/*"
export TRIVY_SKIP_REGISTRY="quay.io"

# Execute Trivy scan
{content}
"""

        super().__init__(
            name=name,
            description=description,
            icon_url=TRIVY_LOGO,
            type="docker",
            image="kubiya/trivy-openshift:latest",
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
        )

def register_trivy_tool(tool):
    tool_registry.register("trivy", tool) 