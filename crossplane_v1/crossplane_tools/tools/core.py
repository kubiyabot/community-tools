from typing import List
from .base import CrossplaneTool, Arg
from kubiya_sdk.tools.registry import tool_registry

"""
Core Operations Module Structure:
"""

class CoreOperations(CrossplaneTool):
    """Core Crossplane operations."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_core",
            description="Core Crossplane operations",
            content="",
            image="bitnami/kubectl:latest",
            mermaid="""
```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class CoreOperations {
        +install_crossplane()
        +uninstall_crossplane()
        +get_status()
        +version()
        +debug_mode()
    }
    CrossplaneTool <|-- CoreOperations
    note for CoreOperations "Manages core Crossplane\ninstallation and operations"
```
"""
        )
        # Register this tool and all core tools
        self.register_tools()

    def register_tools(self):
        """Register all core tools."""
        try:
            # Register the core operations manager itself
            tool_registry.register("crossplane", self)
            
            # Register all core tools
            tools = [
                self.install_crossplane(),
                self.uninstall_crossplane(),
                self.get_status(),
                self.version(),
                self.debug_mode()
            ]
            
            for tool in tools:
                tool_registry.register("crossplane", tool)
                
        except Exception as e:
            print(f"Error registering core tools: {str(e)}")

    def install_crossplane(self) -> CrossplaneTool:
        """Install Crossplane in the cluster."""
        return CrossplaneTool(
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
            image="alpine/helm:3.13.2"  # Using Alpine Helm image for installation
        )

    def uninstall_crossplane(self) -> CrossplaneTool:
        """Uninstall Crossplane from the cluster."""
        return CrossplaneTool(
            name="uninstall_crossplane",
            description="Uninstall Crossplane from the cluster",
            content="""
            # Uninstall Crossplane release
            helm uninstall crossplane --namespace crossplane-system
            
            # Clean up CRDs and namespace
            kubectl delete crds --all --namespace crossplane-system
            kubectl delete namespace crossplane-system
            """,
            image="alpine/helm:3.13.2"
        )

    def get_status(self) -> CrossplaneTool:
        """Get Crossplane system status."""
        return CrossplaneTool(
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
            image="bitnami/kubectl:latest"
        )

    def version(self) -> CrossplaneTool:
        """Get Crossplane version information."""
        return CrossplaneTool(
            name="version",
            description="Get Crossplane version information",
            content="""
            echo "=== Crossplane Version ==="
            kubectl get deployment crossplane -n crossplane-system -o=jsonpath='{.spec.template.spec.containers[0].image}'
            echo "\\n"

            echo "=== Helm Chart Version ==="
            helm list -n crossplane-system
            """,
            image="alpine/helm:3.13.2"
        )

    def debug_mode(self) -> CrossplaneTool:
        """Enable debug mode for Crossplane."""
        return CrossplaneTool(
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
            image="bitnami/kubectl:latest"
        )

# Register tools when module is imported
__all__ = [
    'install_crossplane',
    'uninstall_crossplane',
    'get_status',
    'version',
    'debug_mode'
]

# Remove the separate registration function since tools are registered in the class
if __name__ == "__main__":
    CoreOperations() 