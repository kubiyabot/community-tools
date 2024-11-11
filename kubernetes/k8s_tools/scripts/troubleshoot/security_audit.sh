#!/bin/bash
set -euo pipefail

echo "🔒 Starting Security Audit Analysis..."

# Function to analyze authentication issues
analyze_auth_issues() {
    local namespace="$1"
    local duration="$2"
    
    echo "🔑 Analyzing authentication issues..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "auth-debug" \
        --filter "response.status == 401 or response.status == 403" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Function to analyze TLS/SSL issues
analyze_tls_issues() {
    local namespace="$1"
    local duration="$2"
    
    echo "🔐 Analyzing TLS/SSL issues..."
    
    python /tmp/scripts/kubeshark_capture.py \
        --mode "tls-debug" \
        --filter "protocol.name == 'tls' and error != null" \
        --duration "$duration" \
        --namespace "$namespace"
}

# Main execution
namespace="${1:-default}"
duration="${2:-300}"

analyze_auth_issues "$namespace" "$duration"
analyze_tls_issues "$namespace" "$duration" 