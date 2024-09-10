# k8s_tools/tools/base.py

from kubiya_sdk.tools import Tool
from .common import COMMON_ENVIRONMENT_VARIABLES, COMMON_FILE_SPECS

KUBERNETES_ICON_URL = "https://cdn-icons-png.flaticon.com/256/3889/3889548.png"

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Prepare the content to inject in-cluster context and create a temporary script
        script_content = f"""#!/bin/bash
set -e

# Inject in-cluster context
if [ -f /tmp/kubernetes_context_token ]; then
    # Read the Kubernetes token from the temporary file
    KUBE_TOKEN=$(cat /tmp/kubernetes_context_token)
    # Configure kubectl to use the in-cluster configuration
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster
    kubectl config use-context in-cluster
else
    echo "Error: Kubernetes context token file not found at /tmp/kubernetes_context_token"
    exit 1
fi

# Original content
{content}
"""
        
        # Create a temporary file, write the script to it, and execute it
        full_content = f"""#!/bin/sh
set -e

# Validate cluster permissions by checking for necessary files
if [ ! -f /var/run/secrets/kubernetes.io/serviceaccount/token ]; then
    echo "Error: Kubernetes service account token not found. Are you running inside a Kubernetes cluster?"
    exit 1
fi

if [ ! -f /var/run/secrets/kubernetes.io/serviceaccount/ca.crt ]; then
    echo "Error: Kubernetes CA certificate not found. Are you running inside a Kubernetes cluster?"
    exit 1
fi

# Create a temporary script file
TEMP_SCRIPT=$(mktemp)

# Write the script content to the temporary file
cat << 'EOF' > $TEMP_SCRIPT
{script_content}
EOF

# Make the temporary script executable
chmod +x $TEMP_SCRIPT

# Execute the temporary script
bash $TEMP_SCRIPT

# Clean up by removing the temporary script
rm $TEMP_SCRIPT
"""

        # Initialize the Tool superclass with the prepared content and other parameters
        super().__init__(
            name=name,
            description=description,
            #icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=COMMON_ENVIRONMENT_VARIABLES,
            files=COMMON_FILE_SPECS,
        )
