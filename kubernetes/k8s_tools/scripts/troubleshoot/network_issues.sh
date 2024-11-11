#!/bin/bash
set -euo pipefail

echo "🔍 Starting Network Troubleshooting Analysis..."

# Function to analyze network connectivity issues
analyze_network_connectivity() {
    local namespace="$1"
    local duration="$2"
    
    echo "📡 Analyzing network connectivity in namespace: $namespace"
    
    # Capture connection timeouts and refused connections
    python /tmp/scripts/kubeshark_capture.py \
        --mode "network-debug" \
        --filter "error contains 'timeout' or error contains 'connection refused'" \
        --duration "$duration" \
        --namespace "$namespace"
        
    # Analyze DNS issues
    python /tmp/scripts/kubeshark_capture.py \
        --mode "dns-debug" \
        --filter "protocol.name == 'dns' and response.status != 'NOERROR'" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Function to detect service mesh issues
analyze_service_mesh() {
    local namespace="$1"
    local duration="$2"
    
    echo "🕸️ Analyzing service mesh behavior..."
    
    # Capture service mesh specific issues
    python /tmp/scripts/kubeshark_capture.py \
        --mode "mesh-debug" \
        --filter "protocol.name == 'http' and (response.status >= 500 or response.status == 503)" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Main execution
namespace="${1:-default}"
duration="${2:-300}"

analyze_network_connectivity "$namespace" "$duration"
analyze_service_mesh "$namespace" "$duration" 