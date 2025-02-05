# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

KUBERNETES_ICON_URL = "https://kubernetes.io/icons/icon-128x128.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Basic helper functions that don't interfere with the main script
        helpers = """
# Set up temp directory first, before anything else runs
export TMPDIR="/dev/shm"

# Helper functions
truncate_output() {
    local max_items=${1:-50}
    local max_width=${2:-120}
    awk -v max_items="$max_items" -v max_width="$max_width" '
    NR <= max_items {
        if (length($0) > max_width) {
            print substr($0, 1, max_width-3) "..."
        } else {
            print
        }
    }
    NR == max_items+1 {
        print "... output truncated ..."
    }'
}

# Helper function to safely get parameter values with defaults
get_param() {
    local param_name="$1"
    local default_value="${2:-}"
    
    # Use eval to check if the parameter exists
    if eval "[ ! -z \${$param_name+x} ]"; then
        eval "echo \$$param_name"
    else
        echo "$default_value"
    fi
}

# Setup working directories
setup_dirs() {
    # Create a unique working directory in our TMPDIR
    WORK_DIR="$TMPDIR/kubectl-$(date +%s)-$$"
    mkdir -p "$WORK_DIR"
    echo "$WORK_DIR"
}
"""

        # Simple and robust context injection without chmod
        inject_kubernetes_context = """
set -eu

# Setup working directories and get the work dir path
WORK_DIR=$(setup_dirs)

# Use service account files directly from their original location
TOKEN_LOCATION="/var/run/secrets/kubernetes.io/serviceaccount/token"
CERT_LOCATION="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

# Set KUBECONFIG to a writable location
export KUBECONFIG="$WORK_DIR/config"

# Inject in-cluster context using the service account token directly
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                          --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "Error: Kubernetes service account token or cert not found at $TOKEN_LOCATION or $CERT_LOCATION"
    exit 1
fi

# Cleanup function
cleanup() {
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT
"""
        # Combine helpers and the actual content
        full_content = f"{helpers}\n{inject_kubernetes_context}\n{content}"

        # Mount service account files directly to their expected locations
        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/var/run/secrets/kubernetes.io/serviceaccount/token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            with_files=file_specs,
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
