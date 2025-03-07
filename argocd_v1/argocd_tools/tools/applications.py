from typing import List
from .base import ArgoCDTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys

class ApplicationManager:
    """Manage ArgoCD applications."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Register all tools
            tools = [
                self.create_application(),
                self.list_applications(),
                self.sync_application(),
                self.get_application_logs(),
                self.get_application_details(),
                self.refresh_application(),
                self.list_outdated_applications(),
                self.get_application_history(),
                self.get_health_status()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register ArgoCD tools: {str(e)}", file=sys.stderr)
            raise

    def create_application(self) -> ArgoCDTool:
        """Create a new ArgoCD application."""
        return ArgoCDTool(
            name="create_application",
            description="Create a new ArgoCD application",
            content="""
            if [ -z "$APP_NAME" ] || [ -z "$REPO_URL" ]; then
                echo "Error: Application name and repository URL are required"
                exit 1
            fi

            # Create application using ArgoCD CLI
            argocd app create "$APP_NAME" \
                --repo "$REPO_URL" \
                --path "$PATH" \
                --dest-server "$DEST_SERVER" \
                --dest-namespace "$DEST_NAMESPACE" \
                --sync-policy "$SYNC_POLICY" \
                --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application",
                    required=True),
                Arg(name="repo_url",
                    description="Git repository URL",
                    required=True),
                Arg(name="path",
                    description="Path in repository",
                    required=True),
                Arg(name="dest_server",
                    description="Destination server",
                    required=True),
                Arg(name="dest_namespace",
                    description="Destination namespace",
                    required=True),
                Arg(name="sync_policy",
                    description="Sync policy (manual/automated)",
                    required=False)
            ]
        )

    def list_applications(self) -> ArgoCDTool:
        """List ArgoCD applications."""
        return ArgoCDTool(
            name="list_applications",
            description="List ArgoCD applications",
            content="""
            # List all applications
            argocd app list --insecure --output json || {
                echo "Failed to list applications"
                exit 1
            }
            """,
            args=[]
        )

    def sync_application(self) -> ArgoCDTool:
        """Sync an ArgoCD application."""
        return ArgoCDTool(
            name="sync_application",
            description="Sync an ArgoCD application",
            content="""
            if [ -z "$APP_NAME" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Sync application using ArgoCD CLI
            argocd app sync "$APP_NAME" ${PRUNE:+--prune} ${FORCE:+--force} --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application to sync",
                    required=True),
                Arg(name="prune",
                    description="Prune resources",
                    required=False),
                Arg(name="force",
                    description="Force sync operation",
                    required=False)
            ]
        )

    def get_application_logs(self) -> ArgoCDTool:
        """Get logs from an application's pods."""
        return ArgoCDTool(
            name="get_application_logs",
            description="Get logs from an application's pods",
            content="""
            if [ -z "$APP_NAME" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi
            argocd app logs "$APP_NAME" ${CONTAINER:+--container $CONTAINER} ${FOLLOW:+--follow} --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application",
                    required=True),
                Arg(name="container",
                    description="Container name (if multiple containers)",
                    required=False),
                Arg(name="follow",
                    description="Follow log output",
                    required=False)
            ]
        )
    
    def get_application_details(self) -> ArgoCDTool:
        """Get details of an ArgoCD application."""
        return ArgoCDTool(
            name="get_application_details",
            description="Get detailed information about an ArgoCD application",
            content="""
            if [ -z "$APP_NAME" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get application details
            argocd app get "$APP_NAME" --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application",
                    required=True)
            ]
        )
    
    def refresh_application(self) -> ArgoCDTool:
        """Refresh an ArgoCD application."""
        return ArgoCDTool(
            name="refresh_application",
            description="Refresh ArgoCD cache for an application",
            content="""
            if [ -z "$APP_NAME" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Refresh application cache
            argocd app get "$APP_NAME" --refresh --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application",
                    required=True)
            ]
        )

    def list_outdated_applications(self) -> ArgoCDTool:
        """List all applications that are out-of-sync."""
        return ArgoCDTool(
            name="list_outdated_applications",
            description="List all ArgoCD applications that are out-of-sync",
            content="""
            # List applications that are out of sync
            argocd app list --output json | jq -r '.items[] | select(.status.sync.status!="Synced") | .metadata.name'
            """,
            args=[]
        )
    
    def get_application_history(self) -> ArgoCDTool:
        """Get deployment history for an application."""
        return ArgoCDTool(
            name="get_application_history",
            description="List past revisions of an application",
            content="""
            if [ -z "$APP_NAME" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get deployment history
            argocd app history "$APP_NAME" --insecure
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application",
                    required=True)
            ]
        )


    def get_health_status(self) -> ArgoCDTool:
        """List health status of all applications."""
        return ArgoCDTool(
            name="get_health_status",
            description="List health status of all ArgoCD applications",
            content="""
            # Get application health status
            argocd app list --output json | jq -r '.[] | {name: .metadata.name, health: .status.health.status}'
            """,
            args=[]
        )



# Initialize when module is imported
ApplicationManager() 