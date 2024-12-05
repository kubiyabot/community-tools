# Error Messages and Prompts

## Installation Errors
KUBECTL_MISSING="kubectl not found. Please install kubectl first."
HELM_MISSING="helm not found. Please install helm first."
KUBEWATCH_INSTALL_FAILED="Failed to install kubewatch. Check helm repository and values."

## Configuration Errors  
CONFIG_MISSING="kubewatch configuration file not found at {path}"
INVALID_CONFIG="Invalid kubewatch configuration: {error}"
NAMESPACE_ERROR="Failed to create/access namespace: {error}"

## Runtime Errors
PERMISSION_ERROR="Insufficient permissions: {error}"
CONNECTION_ERROR="Failed to connect to cluster: {error}"
RESOURCE_ERROR="Failed to manage resource {name}: {error}"

## Success Messages
INSTALL_SUCCESS="✅ Successfully installed {component}"
CONFIG_SUCCESS="✅ Successfully configured {component}"
DEPLOY_SUCCESS="✅ Successfully deployed {component}" 