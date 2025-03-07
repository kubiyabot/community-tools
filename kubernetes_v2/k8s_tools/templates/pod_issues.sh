#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')

case "$ACTION" in
  resource-limits)
    echo "Checking for pods without resource limits..."
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': Resources: '}{.spec.containers[*].resources}{'\n'}{end}"
    ;;
  privileged)
    echo "Checking for privileged pods..."
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': Privileged: '}{.spec.containers[*].securityContext.privileged}{'\n'}{end}"
    ;;
  host-network)
    echo "Checking for pods with host network access..."
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': HostNetwork: '}{.spec.hostNetwork}{'\n'}{end}"
    ;;
  all)
    echo "Checking for all pod issues..."
    echo -e "\nPods without resource limits:"
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': Resources: '}{.spec.containers[*].resources}{'\n'}{end}"
    
    echo -e "\nPrivileged pods:"
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': Privileged: '}{.spec.containers[*].securityContext.privileged}{'\n'}{end}"
    
    echo -e "\nPods with host network access:"
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.namespace}{':'}{.metadata.name}{': HostNetwork: '}{.spec.hostNetwork}{'\n'}{end}"
    ;;
  *)
    echo "Error: Invalid action. Supported actions are resource-limits, privileged, host-network, all" >&2
    exit 1
    ;;
esac