#!/bin/sh

# Source utility functions
. /tmp/scripts/utils.sh

# Function to setup kubectl and discover Dagger engine
setup_dagger_engine() {
    log "🔧" "Setting up kubectl..."
    
    # Download kubectl if needed
    if ! command -v kubectl >/dev/null 2>&1; then
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" >/dev/null 2>&1
        chmod +x kubectl
        mv kubectl /usr/local/bin/
    fi

    # Setup kubectl config using service account token
    if [ ! -f "/var/run/secrets/kubernetes.io/serviceaccount/token" ]; then
        log "❌" "Kubernetes service account token not found"
        return 1
    fi

    # Create kubeconfig
    mkdir -p ~/.kube
    cat > ~/.kube/config <<EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    server: https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}
  name: in-cluster
contexts:
- context:
    cluster: in-cluster
    user: in-cluster
  name: in-cluster
current-context: in-cluster
users:
- name: in-cluster
  user:
    token: $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
EOF

    # Test kubectl connection
    if ! kubectl get ns >/dev/null 2>&1; then
        log "❌" "Failed to configure kubectl"
        return 1
    fi
    
    log "✅" "kubectl configured successfully"

    # Find the Dagger Engine pod
    log "🔍" "Discovering Dagger Engine..."
    
    # Find the oldest Dagger Engine pod
    DAGGER_ENGINE_POD_NAME=$(kubectl get pod -n dagger \
        --selector=name=dagger-dagger-helm-engine \
        --sort-by=.metadata.creationTimestamp \
        --output=jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$DAGGER_ENGINE_POD_NAME" ]; then
        log "❌" "No Dagger Engine pod found"
        return 1
    fi

    # Set up Dagger connection
    export DAGGER_ENGINE_POD_NAME
    export _EXPERIMENTAL_DAGGER_RUNNER_HOST="kube-pod://$DAGGER_ENGINE_POD_NAME?namespace=dagger"

    log "✅" "Discovered Dagger Engine pod: $DAGGER_ENGINE_POD_NAME"
    log "✅" "Dagger connection configured: $_EXPERIMENTAL_DAGGER_RUNNER_HOST"
    return 0
}

# Run the setup
setup_dagger_engine