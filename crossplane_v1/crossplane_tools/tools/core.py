"""Core Operations Module

This module provides core Crossplane operations tools.
"""
from typing import List
from .base import CrossplaneTool, Arg
import logging

logger = logging.getLogger(__name__)

# Install Crossplane tool
install_crossplane_tool = CrossplaneTool(
    name="install_crossplane",
    description="Install Crossplane in the cluster",
    content="""
    # Add Helm repo and update
    helm repo add crossplane-stable https://charts.crossplane.io/stable
    helm repo update

    # Create namespace and install Crossplane
    kubectl create namespace crossplane-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Crossplane using Helm
    helm install crossplane crossplane-stable/crossplane \
        --namespace crossplane-system \
        --set args='{--enable-external-secret-stores}' \
        --wait \
        --timeout 300s

    # Wait for Crossplane to be ready
    kubectl wait --for=condition=ready pod -l app=crossplane --namespace crossplane-system --timeout=300s
    """,
    args=[
        Arg(name="timeout", description="Installation timeout in seconds", required=False),
        Arg(name="verify", description="Verify installation", required=False)
    ],
    image="alpine/helm:3.13.2"
)

# Uninstall Crossplane tool
uninstall_crossplane_tool = CrossplaneTool(
    name="uninstall_crossplane",
    description="Uninstall Crossplane from the cluster",
    content="""
    # Uninstall Crossplane release
    helm uninstall crossplane --namespace crossplane-system
    
    # Clean up CRDs and namespace
    kubectl delete crds --all --namespace crossplane-system
    kubectl delete namespace crossplane-system
    """,
    args=[
        Arg(name="verify", description="Verify uninstallation", required=False)
    ],
    image="alpine/helm:3.13.2"
)

# Get status tool
get_status_tool = CrossplaneTool(
    name="get_status",
    description="Get Crossplane system status",
    content="""
    echo "=== Crossplane Pods Status ==="
    kubectl get pods -n crossplane-system

    echo "\\n=== Crossplane Controllers Status ==="
    kubectl get deployment -n crossplane-system

    echo "\\n=== Installed Providers ==="
    kubectl get providers.pkg.crossplane.io --all-namespaces

    echo "\\n=== System Health ==="
    kubectl get events -n crossplane-system --sort-by='.lastTimestamp'
    """,
    args=[
        Arg(name="show_events", description="Show system events", required=False),
        Arg(name="show_health", description="Show health status", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Version tool
version_tool = CrossplaneTool(
    name="version",
    description="Get Crossplane version information",
    content="""
    echo "=== Crossplane Version ==="
    kubectl get deployment crossplane -n crossplane-system -o=jsonpath='{.spec.template.spec.containers[0].image}'
    echo "\\n"

    echo "=== Helm Chart Version ==="
    helm list -n crossplane-system
    """,
    args=[],
    image="alpine/helm:3.13.2"
)

# Debug mode tool
debug_mode_tool = CrossplaneTool(
    name="debug_mode",
    description="Enable debug mode for Crossplane",
    content="""
    echo "=== Enabling Debug Mode ==="
    
    # Update Crossplane deployment to use debug logging
    kubectl patch deployment crossplane -n crossplane-system --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--debug"}]'
    
    # Restart the Crossplane pods
    kubectl rollout restart deployment crossplane -n crossplane-system
    
    echo "\\n=== Waiting for pods to restart ==="
    kubectl rollout status deployment crossplane -n crossplane-system
    
    echo "\\n=== Debug Mode Enabled ==="
    """,
    args=[
        Arg(name="level", description="Debug level (debug, trace)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

def create_core_tools() -> List[CrossplaneTool]:
    """Create and register core Crossplane tools."""
    tools = []
    
    try:
        # Create core tools
        core_tools = {
            'install': install_crossplane_tool,
            'uninstall': uninstall_crossplane_tool,
            'status': get_status_tool,
            'version': version_tool,
            'debug': debug_mode_tool
        }

        # Add all core tools
        for name, tool in core_tools.items():
            tools.append(tool)
            logger.info(f"Added core tool: {name}")

        # Register all created tools
        CrossplaneTool.register_tools(tools)
        logger.info(f"Successfully registered {len(tools)} core tools")
        
    except Exception as e:
        logger.error(f"Failed to create core tools: {str(e)}")
    
    return tools

# Create core tools when module is imported
core_tools = create_core_tools()

# Export tools
__all__ = [
    'install_crossplane_tool',
    'uninstall_crossplane_tool',
    'get_status_tool',
    'version_tool',
    'debug_mode_tool',
    'create_core_tools'
] 