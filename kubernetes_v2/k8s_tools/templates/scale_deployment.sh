#!/bin/bash
set -euo pipefail

# Sanitize inputs
DEPLOYMENT=$(echo "$deployment" | sed 's/[^a-zA-Z0-9-]//g')
REPLICAS=$(echo "$replicas" | sed 's/[^0-9]//g')

kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" scale deployment "$DEPLOYMENT" --replicas="$REPLICAS"

echo "Deployment $DEPLOYMENT scaled to $REPLICAS replicas"