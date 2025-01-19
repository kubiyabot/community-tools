#!/bin/bash
set -e

# Helper function for logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Helper function to check if resource exists in kubernetes
resource_exists() {
    local namespace=$1
    local resource_type=$2
    local resource_name=$3
    kubectl get -n "$namespace" "$resource_type" "$resource_name" &> /dev/null
}

# Get secret value from kubernetes
get_secret_value() {
    local namespace=$1
    local secret_name=$2
    local key=$3
    kubectl get secret -n "$namespace" "$secret_name" -o jsonpath="{.data.$key}" 2>/dev/null || echo ""
}

# Update secret value in kubernetes
update_secret_value() {
    local namespace=$1
    local secret_name=$2
    local key=$3
    local value=$4
    kubectl patch secret -n "$namespace" "$secret_name" -p="{\"data\":{\"$key\":\"$value\"}}"
}

# Restart deployment
restart_deployment() {
    local namespace=$1
    local deployment=$2
    kubectl rollout restart deployment -n "$namespace" "$deployment"
    kubectl rollout status deployment -n "$namespace" "$deployment"
}

# Check for existing enforcer deployment and handle OPA policy updates
check_existing_enforcer() {
    log "Checking if enforcer deployment exists..."
    if resource_exists "kubiya" "deployment" "enforcer"; then
        log "⚠️ Enforcer deployment exists in kubiya namespace - checking OPA policy..."

        local current_policy=$(get_secret_value "kubiya" "enforcer" "OPA_DEFAULT_POLICY")

        if [ -z "$current_policy" ]; then
            log "❌ Error: Could not retrieve current OPA_DEFAULT_POLICY"
            exit 1
        }

        if [ "$current_policy" = "$BS64_OPA_DEFAULT_POLICY" ]; then
            log "✅ OPA_DEFAULT_POLICY is up to date - no changes needed"
            exit 0
        else
            log "🔄 Updating OPA_DEFAULT_POLICY..."
            update_secret_value "kubiya" "enforcer" "OPA_DEFAULT_POLICY" "$BS64_OPA_DEFAULT_POLICY"
            log "🔄 Restarting enforcer deployment..."
            restart_deployment "kubiya" "enforcer"
            log "✅ OPA_DEFAULT_POLICY updated and enforcer restarted successfully"
            exit 0
        fi
    fi
    log "✅ No existing enforcer deployment found - proceeding with installation"
}

# Install required system tools
install_required_tools() {
    log "🚀 Installing required tools..."
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
                    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/stable.txt)/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    mv kubectl /usr/local/bin/
                    ;;
            esac
            log "✅ $cmd installed successfully"
        else
            log "✅ $cmd is already installed"
        fi
    done
}

# Verify cluster connectivity
verify_cluster() {
    log "Testing cluster connection..."
    if ! kubectl cluster-info &> /dev/null; then
        log "❌ Error: Cannot connect to cluster"
        exit 1
    fi
    log "✅ Connected to cluster"
}

# Setup kubiya namespace
setup_namespace() {
    log "Setting up kubiya namespace..."
    if ! resource_exists "" "namespace" "kubiya"; then
        kubectl create namespace kubiya
        log "✅ Created kubiya namespace"
    else
        log "✅ Kubiya namespace already exists"
    fi
}

# Build secret data based on configuration
build_secret_data() {
    local secret_data="  ORG_NAME: $BS64_ORG_NAME
  RUNNER_NAME: $BS64_RUNNER_NAME
  OPA_DEFAULT_POLICY: $BS64_OPA_DEFAULT_POLICY"

    # Add optional DataDog configuration
    if [ ! -z "$BS64_DATA_DOG_API_KEY" ]; then
        secret_data+="\n  DD_API_KEY: $BS64_DATA_DOG_API_KEY"
        log "✅ Added DD_API_KEY to configuration"
    fi
    if [ ! -z "$BS64_DATA_DOG_SITE" ]; then
        secret_data+="\n  DD_SITE: $BS64_DATA_DOG_SITE"
        log "✅ Added DD_SITE to configuration"
    fi

    # Add Okta configuration if needed
    if [ "$IDP_PROVIDER" = "okta" ]; then
        secret_data+="\n  OKTA_BASE_URL: $BS64_OKTA_BASE_URL
  OKTA_TOKEN_ENDPOINT: $BS64_OKTA_TOKEN_ENDPOINT
  OKTA_CLIENT_ID: $BS64_OKTA_CLIENT_ID
  OKTA_PRIVATE_KEY: $BS64_PRIVATE_KEY"
        log "✅ Added Okta configuration"
    fi

    echo -e "$secret_data"
}

# Build environment variables for deployment
build_env_config() {
    local env_config=""
    if [ "$IDP_PROVIDER" = "okta" ]; then
        env_config=$(cat <<EOF
          env:
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
            - name: OKTA_PRIVATE_KEY
              value: /etc/okta/private.pem
            - name: IDP_PROVIDER_NAME
              value: okta
EOF
        )
    else
        env_config=$(cat <<EOF
          env:
            - name: IDP_PROVIDER_NAME
              value: kubiya
EOF
        )
    fi

    # Add common environment variables
    env_config+="\n            - name: NATS_CREDS_FILE
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

    echo "$env_config"
}

# Build volume configuration
build_volume_config() {
    local volume_config=""
    if [ "$IDP_PROVIDER" = "okta" ]; then
        volume_config=$(cat <<EOF
          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/okta/private.pem
              subPath: private.pem
            - name: nats-creds
              readOnly: true
              mountPath: /etc/nats
      volumes:
        - name: private-key-volume
          secret:
            secretName: enforcer
        - name: nats-creds
          secret:
            secretName: nats-creds-runner
            items:
              - key: nats.creds
                path: nats.creds
EOF
        )
    else
        volume_config=$(cat <<EOF
          volumeMounts:
            - name: nats-creds
              readOnly: true
              mountPath: /etc/nats
      volumes:
        - name: nats-creds
          secret:
            secretName: nats-creds-runner
            items:
              - key: nats.creds
                path: nats.creds
EOF
        )
    fi
    echo "$volume_config"
}

# Deploy enforcer components
deploy_enforcer() {
    log "Deploying Enforcer components..."

    local secret_data=$(build_secret_data)
    local env_config=$(build_env_config)
    local volume_config=$(build_volume_config)

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: enforcer
  namespace: kubiya
type: Opaque
data:
$secret_data
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
          image: ghcr.io/kubiyabot/opawatchdog:95ee023db2d0ccdfe9b32c24a602e44d6588d6c6
$env_config
          ports:
            - containerPort: 5001
$volume_config
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
    log "✅ Applied Enforcer resources successfully"
}

# Update tool-manager configuration
update_tool_manager() {
    log "Checking tool-manager configuration..."

    # Check if the environment variable already exists
    local env_exists=$(kubectl get deployment tool-manager -n kubiya -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="KUBIYA_AUTH_SERVER_URL")]}')

    if [ -n "$env_exists" ]; then
        log "✅ KUBIYA_AUTH_SERVER_URL already configured in tool-manager"
        return 0
    fi

    log "Adding KUBIYA_AUTH_SERVER_URL to tool-manager..."
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
    log "✅ Tool manager updated successfully"
}

main() {
    install_required_tools
    check_existing_enforcer
    verify_cluster
    setup_namespace
    deploy_enforcer
    update_tool_manager
    log "✅ Enforcer deployment completed successfully!"
}

main