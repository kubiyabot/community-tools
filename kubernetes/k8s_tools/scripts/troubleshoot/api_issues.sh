#!/bin/bash
set -euo pipefail

echo "🔍 Starting API Troubleshooting Analysis..."

# Function to analyze API latency issues
analyze_api_latency() {
    local namespace="$1"
    local threshold="$2"
    local duration="$3"
    
    echo "⏱️ Analyzing API latency issues..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "api-latency" \
        --filter "protocol.name == 'http' and elapsedTime > $threshold" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Function to analyze API errors
analyze_api_errors() {
    local namespace="$1"
    local duration="$2"
    
    echo "❌ Analyzing API errors..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "api-errors" \
        --filter "protocol.name == 'http' and response.status >= 400" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Main execution
namespace="${1:-default}"
threshold="${2:-1000}"  # Default 1s threshold
duration="${3:-300}"

analyze_api_latency "$namespace" "$threshold" "$duration"
analyze_api_errors "$namespace" "$duration" 