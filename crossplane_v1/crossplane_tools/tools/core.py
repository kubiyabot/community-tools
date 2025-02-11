from typing import List
from .base import CrossplaneTool, Arg

"""
Core Operations Module Structure:

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

class CoreOperations(CrossplaneTool):
    """Core Crossplane operations."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_core",
            description="Core Crossplane operations",
            content="",
            args=[],
            image="bitnami/kubectl:latest",  # Using bitnami's kubectl image for core operations
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
            args=[],
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
            args=[],
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

            echo "\n=== Crossplane Controllers Status ==="
            kubectl get deployment -n crossplane-system

            echo "\n=== Installed Providers ==="
            kubectl get providers.pkg.crossplane.io --all-namespaces

            echo "\n=== System Health ==="
            kubectl get events -n crossplane-system --sort-by='.lastTimestamp'
            """,
            args=[],
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
            echo "\n"

            echo "=== Helm Chart Version ==="
            helm list -n crossplane-system
            """,
            args=[],
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
            
            echo "\n=== Waiting for pods to restart ==="
            kubectl rollout status deployment crossplane -n crossplane-system
            
            echo "\n=== Debug Mode Enabled ==="
            """,
            args=[],
            image="bitnami/kubectl:latest"
        ) 