#!/bin/bash
set -euo pipefail

echo "🚨 Starting Real-time Alert Monitoring..."

# Function to monitor error spikes
monitor_error_spikes() {
    local namespace="$1"
    local threshold="$2"
    local window="$3"
    
    echo "📈 Monitoring error rate spikes..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "error-monitor" \
        --filter "response.status >= 500" \
        --threshold "$threshold" \
        --window "$window" \
        --namespace "$namespace"
}

# Function to monitor latency spikes
monitor_latency_spikes() {
    local namespace="$1"
    local threshold="$2"
    local window="$3"
    
    echo "⏱️ Monitoring latency spikes..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "latency-monitor" \
        --filter "elapsedTime > $threshold" \
        --window "$window" \
        --namespace "$namespace"
}

# Main execution
namespace="${1:-default}"
error_threshold="${2:-10}"    # Default 10 errors per window
latency_threshold="${3:-1000}" # Default 1s
window="${4:-60}"            # Default 60s window

monitor_error_spikes "$namespace" "$error_threshold" "$window"
monitor_latency_spikes "$namespace" "$latency_threshold" "$window" 