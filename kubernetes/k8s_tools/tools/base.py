# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

KUBERNETES_ICON_URL = "https://static-00.iconduck.com/assets.00/kubernetes-icon-512x499-3mjeet3c.png"

class KubernetesTool(Tool):
    def __init__(
        self, 
        name, 
        description, 
        content, 
        args=None, 
        env=None,
        secrets=None,
        file_specs=None,
        image="bitnami/kubectl:latest",
        mermaid=None
    ):
        # Common environment variables
        common_env = [
            "SLACK_CHANNEL_ID",
            "SLACK_THREAD_TS",
        ]
        if env:
            common_env.extend(env)

        # Common secrets
        common_secrets = [
            "SLACK_API_TOKEN",
        ]
        if secrets:
            common_secrets.extend(secrets)

        # Common file specs
        common_file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
            )
        ]
        if file_specs:
            common_file_specs.extend(file_specs)

        # Base content with context injection
        inject_kubernetes_context = """
set -eu
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"

# Export Slack configuration from secrets
export SLACK_API_TOKEN="$(cat /tmp/secrets/SLACK_API_TOKEN 2>/dev/null || echo '')"

# Install required Python packages
pip install argparse slack_sdk websocket-client pyyaml > /dev/null 2>&1

# Inject in-cluster context
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                        --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "Error: Kubernetes context token or cert file not found"
    exit 1
fi
"""
        full_content = f"{inject_kubernetes_context}\n{content}"

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args or [],
            env=common_env,
            secrets=common_secrets,
            with_files=common_file_specs,
            mermaid=mermaid,
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
