#!/bin/bash
# Kubernetes context injection script

# Define locations
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"

# Verify required files exist and are readable
if [ ! -f "$TOKEN_LOCATION" ]; then
    echo "❌ Error: Kubernetes token file not found at $TOKEN_LOCATION" >&2
    exit 1
fi

if [ ! -f "$CERT_LOCATION" ]; then
    echo "❌ Error: Kubernetes certificate file not found at $CERT_LOCATION" >&2
    exit 1
fi

if [ ! -r "$TOKEN_LOCATION" ]; then
    echo "❌ Error: Kubernetes token file is not readable at $TOKEN_LOCATION" >&2
    exit 1
fi

if [ ! -r "$CERT_LOCATION" ]; then
    echo "❌ Error: Kubernetes certificate file is not readable at $CERT_LOCATION" >&2
    exit 1
fi

# Read token securely
KUBE_TOKEN=$(cat "$TOKEN_LOCATION")
if [ -z "$KUBE_TOKEN" ]; then
    echo "❌ Error: Kubernetes token file is empty" >&2
    exit 1
fi

# Configure kubectl with proper error handling
echo "🔧 Configuring Kubernetes context..."

if ! kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                       --certificate-authority="$CERT_LOCATION" >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes cluster configuration" >&2
    exit 1
fi

if ! kubectl config set-credentials in-cluster --token="$KUBE_TOKEN" >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes credentials" >&2
    exit 1
fi

if ! kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster >/dev/null 2>&1; then
    echo "❌ Error: Failed to set Kubernetes context" >&2
    exit 1
fi

if ! kubectl config use-context in-cluster >/dev/null 2>&1; then
    echo "❌ Error: Failed to switch to in-cluster context" >&2
    exit 1
fi

# Verify connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Error: Failed to verify Kubernetes cluster connection" >&2
    exit 1
fi

echo "✅ Successfully configured Kubernetes context" 