#!/bin/bash
set -euo pipefail

if [ -n "${namespace:-}" ]; then
    kubectl $KUBECTL_AUTH_ARGS get pods --namespace "$namespace" -o wide
else
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o wide
fi