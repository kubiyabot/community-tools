#!/bin/bash
set -e

# Helper function for logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Helper function to check command result
check_command() {
#    if [ $? -ne 0 ]; then
#        log "❌ Error: $1"
#        exit 1
#    fi
    log "✅ $2"
}

# Helper function to check if resource exists
resource_exists() {
    local namespace=$1
    local resource_type=$2
    local resource_name=$3
    kubectl get -n "$namespace" "$resource_type" "$resource_name" &> /dev/null
}


# Install required tools if needed
for cmd in curl kubectl; do
    if ! command -v $cmd &> /dev/null; then
        log "Installing $cmd..."
        case $cmd in
            curl)
                rm -rf /var/lib/apt/lists/*
                apt-get clean
                apt-get update -y
                DEBIAN_FRONTEND=noninteractive apt-get install -y curl
                ;;
            kubectl)
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                chmod +x kubectl
                mv kubectl /usr/local/bin/
                ;;
        esac
        check_command "$cmd installation failed" "$cmd installed successfully"
    else
        log "✅ $cmd is already installed"
    fi
done

# Test cluster connection
log "Testing cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    log "❌ Error: Cannot connect to cluster"
    exit 1
fi
check_command "cluster connection failed" "Connected to cluster"

# Create namespace if it doesn't exist
log "Setting up kubiya namespace..."
if ! kubectl get namespace kubiya &> /dev/null; then
    kubectl create namespace kubiya
    check_command "namespace creation failed" "Created kubiya namespace"
else
    log "✅ Kubiya namespace already exists"
fi

# Build base secret data
SECRET_DATA=$(cat <<EOF
  ORG_NAME: $BS64_ORG_NAME
  RUNNER_NAME: $BS64_RUNNER_NAME
  OPA_DEFAULT_POLICY: $BS64_OPA_DEFAULT_POLICY
EOF
)

# Add DataDog API key if provided
if [ ! -z "$BS64_DATA_DOG_API_KEY" ]; then
    SECRET_DATA+=$(cat <<EOF

  DD_API_KEY: $BS64_DATA_DOG_API_KEY
EOF
)
    log "✅ Added DD_API_KEY to configuration"
fi

# Add DataDog site if provided
if [ ! -z "$BS64_DATA_DOG_SITE" ]; then
    SECRET_DATA+=$(cat <<EOF

  DD_SITE: $BS64_DATA_DOG_SITE
EOF
)
    log "✅ Added DD_SITE to configuration"
fi

# Initialize enforcer environment variables
if [ "$IDP_PROVIDER" = "okta" ]; then
    SECRET_DATA+=$(cat <<EOF

  OKTA_BASE_URL: $BS64_OKTA_BASE_URL
  OKTA_TOKEN_ENDPOINT: $BS64_OKTA_TOKEN_ENDPOINT
  OKTA_CLIENT_ID: $BS64_OKTA_CLIENT_ID
  OKTA_PRIVATE_KEY: $BS64_PRIVATE_KEY
EOF
)
    log "✅ Added Okta configuration"

    ENFORCER_ENV="          env:
            - name: OKTA_BASE_URL
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: OKTA_BASE_URL
            - name: OKTA_TOKEN_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: OKTA_TOKEN_ENDPOINT
            - name: OKTA_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: OKTA_CLIENT_ID
            - name: ORG_NAME
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: ORG_NAME
            - name: RUNNER_NAME
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: RUNNER_NAME
            - name: OPA_DEFAULT_POLICY
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: OPA_DEFAULT_POLICY
            - name: OKTA_PRIVATE_KEY
              value: /etc/okta/private.pem
            - name: IDP_PROVIDER_NAME
              value: okta
            - name: NATS_CREDS_FILE
              value: /etc/nats/nats.creds
            - name: NATS_ENDPOINT
              value: tls://connect.ngs.global"

    if [ ! -z "$DATA_DOG_API_KEY_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_API_KEY
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: DD_API_KEY"
    fi

    if [ ! -z "$DATA_DOG_SITE_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_SITE
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: DD_SITE"
    fi

    ENFORCER_VOLUME_MOUNTS="          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/okta/private.pem
              subPath: private.pem
            - name: nats-creds
              readOnly: true
              mountPath: /etc/nats"

    ENFORCER_VOLUMES="      volumes:
        - name: private-key-volume
          secret:
            secretName: enforcer
        - name: nats-creds
          secret:
            secretName: nats-creds-runner
            items:
              - key: nats.creds
                path: nats.creds"
else
    ENFORCER_ENV="          env:
            - name: IDP_PROVIDER_NAME
              value: kubiya
            - name: NATS_CREDS_FILE
              value: /etc/nats/nats.creds
            - name: NATS_ENDPOINT
              value: tls://connect.ngs.global
            - name: ORG_NAME
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: ORG_NAME
            - name: RUNNER_NAME
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: RUNNER_NAME
            - name: OPA_DEFAULT_POLICY
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: OPA_DEFAULT_POLICY"

    if [ ! -z "$DATA_DOG_API_KEY_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_API_KEY
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: DD_API_KEY"
    fi

    if [ ! -z "$DATA_DOG_SITE_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_SITE
              valueFrom:
                secretKeyRef:
                  name: enforcer
                  key: DD_SITE"
    fi

    ENFORCER_VOLUME_MOUNTS="          volumeMounts:
            - name: nats-creds
              readOnly: true
              mountPath: /etc/nats"
    ENFORCER_VOLUMES="      volumes:
        - name: nats-creds
          secret:
            secretName: nats-creds-runner
            items:
              - key: nats.creds
                path: nats.creds"
fi

# Check if enforcer deployment already exists
log "Checking if enforcer deployment exists..."
if resource_exists "kubiya" "deployment" "enforcer"; then
    log "⚠️ Enforcer deployment already exists in kubiya namespace"

    # Update the secret with new configuration
    log "Updating enforcer secret with new configuration..."
    kubectl delete secret enforcer -n kubiya --ignore-not-found
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: enforcer
  namespace: kubiya
type: Opaque
data:
$SECRET_DATA
EOF
    check_command "Failed to update enforcer secret" "Updated enforcer secret successfully"

    # Restart the enforcer deployment to pick up new configuration
    log "Restarting enforcer deployment to apply new configuration..."
    kubectl rollout restart deployment/enforcer -n kubiya
    check_command "Failed to restart enforcer deployment" "Enforcer restart initiated successfully"
    
    log "✅ Configuration updated and enforcer restart triggered!"
    exit 0
fi

log "✅ No existing enforcer deployment found - proceeding with installation"

# Deploy configuration
log "Deploying Enforcer components..."

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: enforcer
  namespace: kubiya
type: Opaque
data:
$SECRET_DATA
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enforcer
  namespace: kubiya
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enforcer
  template:
    metadata:
      labels:
        app: enforcer
    spec:
      containers:
        - name: enforcer
          image: ghcr.io/kubiyabot/opawatchdog:latest
$ENFORCER_ENV
          ports:
            - containerPort: 5001
$ENFORCER_VOLUME_MOUNTS
$ENFORCER_VOLUMES
---
apiVersion: v1
kind: Service
metadata:
  name: enforcer
  namespace: kubiya
spec:
  ports:
    - name: enforcer
      port: 5001
      targetPort: 5001
  selector:
    app: enforcer
EOF

check_command "Failed to apply Enforcer resources" "Applied Enforcer resources successfully"

# Wait for deployment to be ready
log "Waiting for enforcer deployment to be ready..."
#kubectl rollout status deployment/enforcer -n kubiya
check_command "Deployment rollout failed" "Enforcer deployment is ready"

# Update tool-manager deployment with auth server URL
log "Updating tool-manager with auth server URL..."
kubectl patch deployment tool-manager -n kubiya --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/env/-",
    "value": {
      "name": "KUBIYA_AUTH_SERVER_URL",
      "value": "http://enforcer.kubiya:5001"
    }
  }
]'
check_command "Failed to patch tool-manager deployment" "Tool manager updated successfully"

log "✅ Enforcer deployment completed successfully!"