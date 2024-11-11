#!/bin/bash
set -euo pipefail

echo "🗄️ Starting Database Traffic Analysis..."

# Function to analyze database timeouts
analyze_db_timeouts() {
    local namespace="$1"
    local duration="$2"
    
    echo "⏱️ Analyzing database timeouts..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "db-timeouts" \
        --filter "protocol.name in ['mysql', 'postgres', 'mongodb'] and error contains 'timeout'" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Function to analyze slow queries
analyze_slow_queries() {
    local namespace="$1"
    local threshold="$2"
    local duration="$3"
    
    echo "🐢 Analyzing slow queries..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "db-performance" \
        --filter "protocol.name in ['mysql', 'postgres', 'mongodb'] and elapsedTime > $threshold" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Main execution
namespace="${1:-default}"
threshold="${2:-1000}"  # Default 1s threshold
duration="${3:-300}"

analyze_db_timeouts "$namespace" "$duration"
analyze_slow_queries "$namespace" "$threshold" "$duration" 