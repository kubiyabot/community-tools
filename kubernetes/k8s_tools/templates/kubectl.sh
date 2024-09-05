#!/bin/bash
set -euo pipefail

# Sanitize input
COMMAND=$(echo "$command" | sed 's/[;&|]//g')

# Execute kubectl command
kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" $COMMAND