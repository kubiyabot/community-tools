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
    
    # Use /tmp for all files
    JSON_FILE="${KUBEWATCH_CONFIG_PATH:-/tmp/kubewatch.json}"
    YAML_FILE="/tmp/kubewatch.yaml"
    
    # Convert JSON to YAML using yq
    echo "📝 Converting configuration to YAML..."
    if [ ! -f "$JSON_FILE" ]; then
        echo "❌ JSON configuration file not found at: $JSON_FILE"
        exit 1
    fi
    
    # Use yq to read JSON and output as YAML
    yq eval -P "$JSON_FILE" > "$YAML_FILE" || {
        echo "❌ Failed to convert JSON to YAML"
        echo "JSON content:"
        cat "$JSON_FILE"
        exit 1
    }
    
    echo "Successfully generated KubeWatch configuration, reference:\n\n$(cat "$YAML_FILE")\n\n"

    # Add watch configurations
    if [ "${WATCH_POD:-true}" = "true" ]; then
        yq eval -i '.data[".kubewatch.yaml"].filter.watch_for += {"kind": "Pod", "reasons": ["*CrashLoopBackOff*", "*OOMKilled*", "*ImagePullBackOff*", "*RunContainerError*", "*Failed*"], "severity": "critical"}' "$YAML_FILE" || {
            echo "❌ Failed to add Pod watch configuration"
            exit 1
        }
    fi

    if [ "${WATCH_NODE:-true}" = "true" ]; then
        yq eval -i '.data[".kubewatch.yaml"].filter.watch_for += {"kind": "Node", "reasons": ["*NotReady*", "*DiskPressure*", "*MemoryPressure*", "*NetworkUnavailable*"], "severity": "critical"}' "$YAML_FILE" || {
            echo "❌ Failed to add Node watch configuration"
            exit 1
        }
    fi

    echo "🔄 Applying KubeWatch configuration..."
    if ! kubectl apply -f "$YAML_FILE"; then
        echo "❌ Failed to apply KubeWatch configuration"
        echo "Configuration content:"
        cat "$YAML_FILE"
        exit 1
    fi
    echo "✅ KubeWatch configuration applied successfully - events will be sent to the configured webhook"
else
    echo "ℹ️ No webhook URL provided - skipping KubeWatch configuration (will not be able to watch for events)"
fi

echo "✅ Kubernetes Tools initialized successfully!"
