from typing import Optional
from kubiya_sdk.tools.models import Arg, Tool, FileSpec
from pydantic import HttpUrl

OPENSHIFT_LOGO = HttpUrl(
    "https://dwglogo.com/wp-content/uploads/2017/11/2200px_OpenShift_logo.png"
)

class BaseOCTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list[Arg] = [],
        long_running=False,
    ):
        inject_openshift_context = """
set -e
TOKEN_LOCATION="/tmp/openshift_context_token"
CERT_LOCATION="/tmp/openshift_context_cert"

# Inject in-cluster context using the temporary token file
if [ -f "$TOKEN_LOCATION" ] && [ -f "$CERT_LOCATION" ]; then
    OC_TOKEN=$(cat "$TOKEN_LOCATION")
    
    # Check if K8s environment variables are set, otherwise use default values
    if [ -z "${KUBERNETES_SERVICE_HOST:-}" ] || [ -z "${KUBERNETES_SERVICE_PORT:-}" ]; then
        echo "Warning: KUBERNETES_SERVICE_HOST or KUBERNETES_SERVICE_PORT not set."
        echo "Attempting to find API server information from kubeconfig or using default..."
        
        # Try to extract server info from existing kubeconfig
        if kubectl config view -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null | grep -q "https://"; then
            API_SERVER=$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null)
            echo "Found API server: $API_SERVER"
        else
            # Default to kubernetes.default.svc
            API_SERVER="https://kubernetes.default.svc:443"
            echo "Using default API server: $API_SERVER"
        fi
    else
        API_SERVER="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"
        echo "Using API server from environment: $API_SERVER"
    fi
    
    echo "Attempting to log in to: $API_SERVER"
    if ! oc login "$API_SERVER" --token="$OC_TOKEN" --certificate-authority="$CERT_LOCATION" > /dev/null 2>&1; then
        echo "Error: Failed to login to OpenShift using service account token."
        exit 1
    fi
    
    echo "Successfully logged in to OpenShift"
else
    echo "Error: OpenShift context token or cert file not found at $TOKEN_LOCATION or $CERT_LOCATION respectively."
    exit 1
fi
"""
        # Function to handle output formatting
        output_handler = """
# Function to handle command output and remove ANSI color codes
handle_output() {
    sed 's/\\x1b\\[[0-9;]*[a-zA-Z]//g' | tr -d '\\r' | sed 's/</\\</g' | sed 's/>/\\>/g'
}
"""
        
        full_content = f"{output_handler}\n{inject_openshift_context}\n# Execute the actual command with output handling\n{{\n{content}\n}} 2>&1 | handle_output"

        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/openshift_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/openshift_context_cert"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=OPENSHIFT_LOGO,
            type="docker",
            image="openshift/origin-cli:latest",
            content=full_content,
            args=args,
            with_files=file_specs,
            env=[],
            secrets=[],
            long_running=long_running,
        )
