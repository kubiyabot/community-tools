#!/bin/bash
set -euo pipefail

echo "Node Resource Usage:"
kubectl $KUBECTL_AUTH_ARGS top nodes

echo -e "\nPod Resource Usage:"
if [ -n "${namespace:-}" ]; then
    kubectl $KUBECTL_AUTH_ARGS top pods --namespace "$namespace"
else
    kubectl $KUBECTL_AUTH_ARGS top pods --all-namespaces
fi