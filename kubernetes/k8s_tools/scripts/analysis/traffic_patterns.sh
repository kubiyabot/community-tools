#!/bin/bash
set -euo pipefail

echo "📊 Starting Traffic Pattern Analysis..."

# Function to analyze traffic patterns
analyze_traffic_patterns() {
    local namespace="$1"
    local duration="$2"
    
    echo "🔄 Analyzing traffic patterns..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "traffic-patterns" \
        --duration "$duration" \
        --namespace "$namespace" \
        --aggregate-by "endpoint" \
        --metrics "count,avg_latency,error_rate"
}

# Function to detect anomalies
detect_anomalies() {
    local namespace="$1"
    local duration="$2"
    local threshold="$3"
    
    echo "🔍 Detecting traffic anomalies..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "anomaly-detection" \
        --duration "$duration" \
        --namespace "$namespace" \
        --threshold "$threshold"
}

# Main execution
namespace="${1:-default}"
duration="${2:-3600}"  # Default 1 hour
threshold="${3:-2.0}"  # Default 2 standard deviations

analyze_traffic_patterns "$namespace" "$duration"
detect_anomalies "$namespace" "$duration" "$threshold" 