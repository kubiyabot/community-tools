from typing import List
from .base import CrossplaneTool, Arg

class PackageManager(CrossplaneTool):
    """Manage Crossplane packages."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_package",
            description="Manage Crossplane packages and configurations",
            content="",
            args=[],
            image="bitnami/kubectl:latest"
        )

    def install_package(self) -> CrossplaneTool:
        """Install a Crossplane package."""
        return CrossplaneTool(
            name="install_package",
            description="Install a Crossplane package",
            content="""
            if [ -z "$PACKAGE_NAME" ]; then
                echo "Error: Package name not specified"
                exit 1
            fi

            # Create package installation
            cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: ${PACKAGE_NAME##*/}
spec:
  package: $PACKAGE_NAME
  revisionActivationPolicy: Automatic
  revisionHistoryLimit: 3
EOF

            # Wait for package to be healthy
            echo "Waiting for package to be healthy..."
            kubectl wait --for=condition=healthy configuration.pkg.crossplane.io/${PACKAGE_NAME##*/} --timeout=300s
            """,
            args=[
                Arg("package_name",
                    description="The package to install (e.g., registry.upbound.io/xp/getting-started:v1.9.0)",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def list_packages(self) -> CrossplaneTool:
        """List installed Crossplane packages."""
        return CrossplaneTool(
            name="list_packages",
            description="List installed Crossplane packages",
            content="""
            echo "=== Installed Configurations ==="
            kubectl get configurations.pkg.crossplane.io

            echo "\n=== Configuration Revisions ==="
            kubectl get configurationrevisions.pkg.crossplane.io

            echo "\n=== Package Locks ==="
            kubectl get locks.pkg.crossplane.io
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def get_package_status(self) -> CrossplaneTool:
        """Get detailed status of a specific package."""
        return CrossplaneTool(
            name="get_package_status",
            description="Get detailed status of a specific package",
            content="""
            if [ -z "$PACKAGE_NAME" ]; then
                echo "Error: Package name not specified"
                exit 1
            fi

            echo "=== Package Status ==="
            kubectl describe configuration.pkg.crossplane.io "$PACKAGE_NAME"

            echo "\n=== Package Revisions ==="
            kubectl get configurationrevision.pkg.crossplane.io -l pkg.crossplane.io/configuration="$PACKAGE_NAME"

            echo "\n=== Package Events ==="
            kubectl get events --field-selector involvedObject.kind=Configuration,involvedObject.name="$PACKAGE_NAME" --sort-by='.lastTimestamp'
            """,
            args=[
                Arg("package_name",
                    description="Name of the package to check",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def uninstall_package(self) -> CrossplaneTool:
        """Uninstall a Crossplane package."""
        return CrossplaneTool(
            name="uninstall_package",
            description="Uninstall a Crossplane package",
            content="""
            if [ -z "$PACKAGE_NAME" ]; then
                echo "Error: Package name not specified"
                exit 1
            fi

            echo "Deleting package configuration..."
            kubectl delete configuration.pkg.crossplane.io "$PACKAGE_NAME"

            echo "Cleaning up package revisions..."
            kubectl delete configurationrevision.pkg.crossplane.io -l pkg.crossplane.io/configuration="$PACKAGE_NAME"

            echo "Cleaning up related locks..."
            kubectl delete lock.pkg.crossplane.io -l pkg.crossplane.io/configuration="$PACKAGE_NAME"
            """,
            args=[
                Arg("package_name",
                    description="Name of the package to uninstall",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def upgrade_package(self) -> CrossplaneTool:
        """Upgrade a Crossplane package to a new version."""
        return CrossplaneTool(
            name="upgrade_package",
            description="Upgrade a Crossplane package to a new version",
            content="""
            if [ -z "$PACKAGE_NAME" ] || [ -z "$NEW_VERSION" ]; then
                echo "Error: Package name and new version must be specified"
                exit 1
            fi

            echo "=== Upgrading Package ==="
            
            # Update the package version
            kubectl patch configuration.pkg.crossplane.io "$PACKAGE_NAME" --type=merge -p "{\"spec\":{\"package\":\"$NEW_VERSION\"}}"
            
            echo "Waiting for new version to be healthy..."
            kubectl wait --for=condition=healthy configuration.pkg.crossplane.io/"$PACKAGE_NAME" --timeout=300s
            
            echo "\nCleaning up old revisions..."
            OLD_REVISIONS=$(kubectl get configurationrevision.pkg.crossplane.io -l pkg.crossplane.io/configuration="$PACKAGE_NAME" -o jsonpath='{range .items[?(@.spec.desiredState!="Active")]}{.metadata.name}{"\n"}{end}')
            if [ -n "$OLD_REVISIONS" ]; then
                echo "$OLD_REVISIONS" | xargs kubectl delete configurationrevision.pkg.crossplane.io
            fi
            """,
            args=[
                Arg("package_name",
                    description="Name of the package to upgrade",
                    required=True),
                Arg("new_version",
                    description="New version of the package",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        ) 