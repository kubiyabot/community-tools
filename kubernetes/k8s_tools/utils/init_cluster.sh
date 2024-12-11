#!/bin/bash
set -e

echo "🚀 Initializing Kubernetes Tools..."

# Function to handle errors
handle_error() {
    local exit_code=$?
    local line_no=$1
    echo "❌ Error on line $line_no: Command failed with exit code $exit_code"
    case $exit_code in
        127) echo "  • Command not found - Missing required dependencies" ;;
        1) echo "  • General error occurred" ;;
        *) echo "  • Unexpected error occurred" ;;
    esac
    exit $exit_code
}

# Set error handler
trap 'handle_error $LINENO' ERR

# Function to download file with fallback methods
download_file() {
    local url=$1
    local output=$2
    local downloaded=false

    # Install curl if not available
    if ! command -v curl &> /dev/null; then
        echo "🔧 Installing curl..."
        apt-get update && apt-get install -y curl
    fi

    # Try curl first
    if command -v curl &> /dev/null; then
        echo "📥 Downloading using curl..."
        if curl -fsSL "$url" -o "$output"; then
            downloaded=true
        fi
    fi

    # Fallback to wget if curl failed or doesn't exist
    if [ "$downloaded" = false ] && command -v wget &> /dev/null; then
        echo "📥 Downloading using wget..."
        if wget -q "$url" -O "$output"; then
            downloaded=true
        fi
    fi

    # If both methods failed
    if [ "$downloaded" = false ]; then
        echo "❌ Failed to download file: Neither curl nor wget is available"
        echo "Please install curl or wget and try again"
        exit 1
    fi
}

# Install yq if not available
if ! command -v yq &> /dev/null; then
    echo "🔧 Installing yq..."
    YQ_VERSION="v4.35.1"
    YQ_BINARY="yq_linux_amd64"
    YQ_URL="https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/$YQ_BINARY"
    
    # Download yq
    download_file "$YQ_URL" "/usr/local/bin/yq"
    chmod +x /usr/local/bin/yq || {
        echo "❌ Failed to make yq executable"
        exit 1
    }
fi

# Install kubectl if not available
if ! command -v kubectl &> /dev/null; then
    echo "🔧 Installing kubectl..."
    KUBECTL_URL="https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    
    # Download kubectl
    download_file "$KUBECTL_URL" "/usr/local/bin/kubectl"
    chmod +x /usr/local/bin/kubectl || {
        echo "❌ Failed to make kubectl executable"
        exit 1
    }
fi

# Check for required commands
for cmd in curl chmod mkdir envsubst; do
    if ! command -v $cmd &> /dev/null; then
        echo "🔧 Installing required command: $cmd"
        apt-get update && apt-get install -y gettext-base
    fi
done

# Generate KubeWatch configuration if webhook URL is provided
if [ -n "${KUBIYA_KUBEWATCH_WEBHOOK_URL}" ]; then
    echo "🔄 Configuring KubeWatch..."
    
    # Create config directory if it doesn't exist
    CONFIG_DIR="$(dirname "$0")/../config"
    mkdir -p "$CONFIG_DIR" || {
        echo "❌ Failed to create config directory"
        exit 1
    }
    
    # Generate base KubeWatch configuration
    echo "📝 Generating KubeWatch configuration..."
    cat > "$CONFIG_DIR/kubewatch.yaml" <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubewatch-config
  namespace: default
data:
  .kubewatch.yaml: |
    version: "1"
    filter:
      watch_for: []
      settings:
        dedup_interval: ${DEDUP_WINDOW:-15m}
        include_labels: true
        namespace_isolation: false
        group_by:
          - owner
          - app_label
        log_tail: ${MAX_LOG_LINES:-50}
    handler:
      webhook:
        url: "${KUBIYA_KUBEWATCH_WEBHOOK_URL}"
        batchSize: ${BATCH_SIZE:-5}
        maxWaitTime: "${MAX_WAIT_TIME:-30s}"
        minWaitTime: "${MIN_WAIT_TIME:-5s}"
        groupEvents: true
        groupBy:
          - kind
          - namespace
          - reason
          - owner
        filtering:
          includeRoutineEvents: false
          minSeverity: "${MIN_SEVERITY:-Warning}"
          deduplication:
            enabled: true
            window: "${DEDUP_WINDOW:-15m}"
    resource:
      pod: ${WATCH_POD:-true}
      node: ${WATCH_NODE:-true}
      deployment: ${WATCH_DEPLOYMENT:-true}
      service: ${WATCH_SERVICE:-false}
      ingress: ${WATCH_INGRESS:-false}
      event: ${WATCH_EVENT:-true}
    enrichment:
      include_logs: ${INCLUDE_LOGS:-true}
      include_events: ${INCLUDE_EVENTS:-true}
      include_metrics: ${INCLUDE_METRICS:-true}
      max_log_lines: ${MAX_LOG_LINES:-50}
      max_events: ${MAX_EVENTS:-10}
EOF

    CONFIG_FILE="$CONFIG_DIR/kubewatch.yaml"
    
    # Process environment variables in the configuration
    envsubst < "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    
    echo "Successfully generated KubeWatch configuration, reference:\n\n$(cat "$CONFIG_FILE")\n\n"

    # Add watch configurations using yq
    if [ "${WATCH_POD:-true}" = "true" ]; then
        yq -i '.filter.watch_for += {"kind": "Pod", "reasons": ["*CrashLoopBackOff*", "*OOMKilled*", "*ImagePullBackOff*", "*RunContainerError*", "*Failed*"], "severity": "critical"}' "$CONFIG_DIR/kubewatch.yaml" || {
            echo "❌ Failed to add Pod watch configuration"
            exit 1
        }
    fi

    if [ "${WATCH_NODE:-true}" = "true" ]; then
        yq -i '.filter.watch_for += {"kind": "Node", "reasons": ["*NotReady*", "*DiskPressure*", "*MemoryPressure*", "*NetworkUnavailable*"], "severity": "critical"}' "$CONFIG_DIR/kubewatch.yaml" || {
            echo "❌ Failed to add Node watch configuration"
            exit 1
        }
    fi

    echo "🔄 Applying KubeWatch configuration..."
    kubectl apply -f "$CONFIG_DIR/kubewatch.yaml" || {
        echo "❌ Failed to apply KubeWatch configuration, refer to the generated configuration for reference"
        exit 1
    }
    echo "✅ KubeWatch configuration applied successfully - events will be sent to the configured webhook"
else
    echo "ℹ️ No webhook URL provided - skipping KubeWatch configuration (will not be able to watch for events)"
fi

echo "✅ Kubernetes Tools initialized successfully!"
