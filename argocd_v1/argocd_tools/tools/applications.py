from typing import List
from .base import ArgoCDTool, ArgoCDGitTool, ArgoCDKubeTool, ArgoCDBitbucketTool, Arg
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
                self.get_health_status(),
                self.setup_helm_environment(),
                self.deploy_application(),
                self.prune_resources(),
                self.rollback_application(),
                self.diff_application()
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
            if [ -z "$app_name" ] || [ -z "$repo_url" ]; then
                echo "Error: Application name and repository URL are required"
                exit 1
            fi

            # Create application using ArgoCD CLI
            argocd app create "$app_name" \
                --repo "$repo_url" \
                --path "$path" \
                --dest-server "$dest_server" \
                --dest-namespace "$dest_namespace" \
                --sync-policy "$sync_policy" \
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
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Sync application using ArgoCD CLI
            argocd app sync "$app_name" ${prune:+--prune} ${force:+--force} --insecure
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
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi
            argocd app logs "$app_name" ${container:+--container $container} ${follow:+--follow} --insecure
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
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get application details
            argocd app get "$app_name" --insecure
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
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Refresh application cache
            argocd app get "$app_name" --refresh --insecure
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
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get deployment history
            argocd app history "$app_name" --insecure
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

    def setup_helm_environment(self) -> ArgoCDGitTool:
        """Set up an ArgoCD environment using a Helm chart from a GitHub repository."""
        return ArgoCDGitTool(
            name="setup_helm_environment",
            description="Set up an ArgoCD environment using a Helm chart from a GitHub repository",
            content="""
            if [ -z "$repo_url" ] || [ -z "$chart_path" ]; then
                echo "Error: Repository URL and chart path are required"
                exit 1
            fi

            # Clone the repository
            echo "📦 Cloning repository..."
            git clone "$repo_url" repo || {
                echo "Failed to clone repository"
                exit 1
            }
            cd repo

            # Validate Helm chart
            echo "🔍 Validating Helm chart..."
            if [ ! -d "$chart_path" ]; then
                echo "❌ Chart path '$chart_path' not found in repository"
                exit 1
            fi

            if [ ! -f "$chart_path/Chart.yaml" ]; then
                echo "❌ No Chart.yaml found in '$chart_path'"
                exit 1
            fi

            # Create ArgoCD application
            echo "🚀 Creating ArgoCD application..."
            argocd app create "$app_name" \
                --repo "$repo_url" \
                --path "$chart_path" \
                --dest-server "$dest_server" \
                --dest-namespace "$dest_namespace" \
                $([[ -n "$helm_values" ]] && echo "--helm-set $helm_values") \
                --insecure || {
                echo "Failed to create ArgoCD application"
                exit 1
            }

            # Configure sync policy if automated
            if [ "$sync_policy" = "automated" ]; then
                echo "⚙️ Configuring automated sync policy..."
                argocd app set "$app_name" --sync-policy automated --self-heal --allow-empty --insecure || {
                    echo "Failed to set sync policy"
                    exit 1
                }
            fi

            # Initial sync if auto-sync is not enabled
            if [ "$sync_policy" != "automated" ]; then
                echo "🔄 Performing initial sync..."
                argocd app sync "$app_name" --insecure
            fi

            echo "✅ ArgoCD environment setup completed successfully"
            """,
            args=[
                Arg(name="repo_url",
                    description="GitHub repository URL containing the Helm chart",
                    required=True),
                Arg(name="chart_path",
                    description="Path to the Helm chart within the repository",
                    required=True),
                Arg(name="app_name",
                    description="Name for the ArgoCD application",
                    required=True),
                Arg(name="dest_server",
                    description="Destination Kubernetes cluster server URL",
                    required=True),
                Arg(name="dest_namespace",
                    description="Destination namespace for the application",
                    required=True),
                Arg(name="helm_values",
                    description="Helm values to set (comma-separated key=value pairs, e.g. 'key1=value1,key2=value2')",
                    required=False),
                Arg(name="sync_policy",
                    description="Sync policy (manual/automated)",
                    required=False,
                    default="manual")
            ]
        )

    def deploy_application(self) -> ArgoCDKubeTool:
        """Deploy an ArgoCD application to Kubernetes and monitor its status."""
        return ArgoCDKubeTool(
            name="deploy_application",
            description="Deploy and sync an ArgoCD application to Kubernetes, then monitor its status",
            content="""
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Verify namespace exists
            echo "🔍 Verifying namespace '$namespace' exists..."
            if ! kubectl get namespace "$namespace" &>/dev/null; then
                echo "Creating namespace '$namespace'..."
                kubectl create namespace "$namespace" || {
                    echo "❌ Failed to create namespace '$namespace'"
                    exit 1
                }
            fi

            # Get application details
            echo "🔍 Checking application configuration..."
            app_info=$(argocd app get "$app_name" --insecure -o json)
            repo_url=$(echo "$app_info" | jq -r '.spec.source.repoURL')
            repo_path=$(echo "$app_info" | jq -r '.spec.source.path')
            echo "📁 Source: $repo_url -> $repo_path"

            # Verify repository access
            echo "🔍 Verifying repository access..."
            if ! argocd repo get "$repo_url" --insecure &>/dev/null; then
                echo "⚠️ Repository not registered with ArgoCD"
                argocd repo add "$repo_url" --insecure || {
                    echo "❌ Failed to register repository"
                    exit 1
                }
            fi

            # Force refresh and sync
            echo "🔄 Syncing application..."
            argocd app refresh "$app_name" --insecure
            
            # Check if manifests are being generated
            echo "\n📋 Checking generated manifests..."
            if ! argocd app manifests "$app_name" --insecure | grep -q .; then
                echo "❌ No manifests generated from source"
                echo "🔍 Debugging Helm chart..."
                
                # Clone repo to check Helm chart
                temp_dir=$(mktemp -d)
                git clone "$repo_url" "$temp_dir"
                cd "$temp_dir/$repo_path"
                
                echo "\n📁 Helm chart contents:"
                ls -la
                
                if [ -f "Chart.yaml" ]; then
                    echo "\n📋 Chart.yaml:"
                    cat Chart.yaml
                    echo "\n🔍 Running helm template..."
                    helm template .
                fi
                
                cd - > /dev/null
                rm -rf "$temp_dir"
                exit 1
            fi

            # Sync with force
            if ! argocd app sync "$app_name" --force --prune --replace --insecure; then
                echo "❌ Failed to sync application"
                echo "\n📝 Error details from controller:"
                kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=20 | grep -i "error\\|$app_name"
                exit 1
            fi

            # Monitor deployment
            echo "⏳ Waiting for sync to complete..."
            timeout=300
            elapsed=0
            while [ $elapsed -lt $timeout ]; do
                status=$(argocd app get "$app_name" --insecure -o json | jq -r '.status.sync.status')
                health=$(argocd app get "$app_name" --insecure -o json | jq -r '.status.health.status')
                
                echo "📊 Status: Sync=$status, Health=$health"
                
                if [ "$status" = "Synced" ] && [ "$health" = "Healthy" ]; then
                    # Check for actual resources
                    if kubectl get all -n "$namespace" 2>/dev/null | grep -q .; then
                        echo "✅ Application deployed successfully!"
                        echo "\n📦 Deployed resources:"
                        kubectl get all -n "$namespace"
                        exit 0
                    else
                        echo "⚠️ No resources created despite successful sync"
                        echo "\n📝 Debugging information:"
                        echo "Expected manifests:"
                        argocd app manifests "$app_name" --insecure
                        echo "\nController logs:"
                        kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=20 | grep -i "$app_name"
                        exit 1
                    fi
                fi
                
                if [ "$status" = "OutOfSync" ] || [ "$health" = "Degraded" ]; then
                    echo "⚠️ Application is in a degraded state"
                    argocd app diff "$app_name" --insecure
                    exit 1
                fi
                
                sleep 10
                elapsed=$((elapsed + 10))
            done

            echo "❌ Deployment timed out after ${timeout}s"
            argocd app get "$app_name" --insecure
            exit 1
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the ArgoCD application to deploy",
                    required=True),
                Arg(name="namespace",
                    description="Kubernetes namespace where the application will be deployed",
                    required=True)
            ]
        )

    def prune_resources(self) -> ArgoCDBitbucketTool:
        """Prune resources that have been removed from the source repository."""
        return ArgoCDBitbucketTool(
            name="prune_resources",
            description="Prune resources that have been removed from the source repository (like deleted CronJobs)",
            content="""
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get current application status
            echo "🔍 Checking current application status..."
            app_status=$(argocd app get "$app_name" -o json)
            if [ $? -ne 0 ]; then
                echo "❌ Failed to get application status"
                exit 1
            fi
            
            sync_status=$(echo "$app_status" | jq -r '.status.sync.status')
            echo "Current sync status: $sync_status"
            
            if [ "$sync_status" = "Synced" ]; then
                echo "⚠️ Application is already synced. Forcing refresh to detect changes..."
                argocd app refresh "$app_name"
                if [ $? -ne 0 ]; then
                    echo "❌ Failed to refresh application"
                    exit 1
                fi
                
                # Check again after refresh
                app_status=$(argocd app get "$app_name" -o json)
                sync_status=$(echo "$app_status" | jq -r '.status.sync.status')
                echo "Sync status after refresh: $sync_status"
            fi
            
            # Show resources that will be pruned
            echo "📋 Resources that will be pruned:"
            argocd app diff "$app_name" | grep "^-" || echo "No resources to prune detected in diff"
            
            # Perform sync with prune option
            echo "🔄 Syncing application with prune option..."
            argocd app sync "$app_name" --prune
            if [ $? -ne 0 ]; then
                echo "❌ Failed to sync application with prune option"
                exit 1
            fi
            
            # Verify sync completed successfully
            echo "✅ Sync with prune completed. Verifying application status..."
            app_status=$(argocd app get "$app_name" -o json)
            sync_status=$(echo "$app_status" | jq -r '.status.sync.status')
            health_status=$(echo "$app_status" | jq -r '.status.health.status')
            
            echo "Final status: Sync=$sync_status, Health=$health_status"
            
            if [ "$sync_status" = "Synced" ]; then
                echo "✅ Resources successfully pruned!"
            else
                echo "⚠️ Application is not fully synced after prune operation."
                echo "Please check application details for more information."
            fi
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application to prune resources from",
                    required=True)
            ]
        )

    def rollback_application(self) -> ArgoCDTool:
        """Rollback an application to a previous revision."""
        return ArgoCDTool(
            name="rollback_application",
            description="Rollback an ArgoCD application to a previous revision",
            content="""
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Get application history
            echo "📋 Application revision history:"
            argocd app history "$app_name" --insecure
            
            # If revision is not specified, list history and exit
            if [ -z "$revision" ]; then
                echo "⚠️ No revision specified. Please specify a revision ID from the history above."
                exit 1
            fi
            
            # Perform rollback
            echo "🔄 Rolling back application to revision $revision..."
            argocd app rollback "$app_name" "$revision" --insecure || {
                echo "❌ Failed to rollback application"
                exit 1
            }
            
            # Verify rollback completed successfully
            echo "✅ Rollback initiated. Verifying application status..."
            app_status=$(argocd app get "$app_name" --insecure -o json)
            sync_status=$(echo "$app_status" | jq -r '.status.sync.status')
            health_status=$(echo "$app_status" | jq -r '.status.health.status')
            
            echo "Status after rollback: Sync=$sync_status, Health=$health_status"
            
            if [ "$sync_status" = "Synced" ] && [ "$health_status" = "Healthy" ]; then
                echo "✅ Application successfully rolled back to revision $revision!"
            else
                echo "⚠️ Application is not fully synced or healthy after rollback."
                echo "Please check application details for more information."
            fi
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application to rollback",
                    required=True),
                Arg(name="revision",
                    description="Revision ID to rollback to",
                    required=True)
            ]
        )

    def diff_application(self) -> ArgoCDTool:
        """Show differences between the current state and the desired state."""
        return ArgoCDTool(
            name="diff_application",
            description="Show differences between the current state and the desired state of an ArgoCD application",
            content="""
            if [ -z "$app_name" ]; then
                echo "Error: Application name not specified"
                exit 1
            fi

            # Refresh application to ensure we have the latest state
            echo "🔄 Refreshing application to get latest state..."
            argocd app refresh "$app_name" --insecure || {
                echo "❌ Failed to refresh application"
                exit 1
            }
            
            # Show diff
            echo "📋 Differences between current state and desired state:"
            argocd app diff "$app_name" --insecure
            
            # Get summary of changes
            echo "\n📊 Summary of changes:"
            diff_output=$(argocd app diff "$app_name" --insecure)
            
            # Count additions, modifications, and deletions
            additions=$(echo "$diff_output" | grep -c "^+")
            deletions=$(echo "$diff_output" | grep -c "^-")
            
            echo "Additions: $additions"
            echo "Deletions: $deletions"
            
            # Show sync status
            app_status=$(argocd app get "$app_name" --insecure -o json)
            sync_status=$(echo "$app_status" | jq -r '.status.sync.status')
            echo "\nCurrent sync status: $sync_status"
            
            if [ "$sync_status" = "Synced" ] && [ "$additions" -eq 0 ] && [ "$deletions" -eq 0 ]; then
                echo "✅ Application is in sync with the desired state."
            else
                echo "⚠️ Application is not in sync with the desired state."
                echo "Run 'sync_application' to apply these changes."
            fi
            """,
            args=[
                Arg(name="app_name",
                    description="Name of the application to show differences for",
                    required=True)
            ]
        )



# Initialize when module is imported
ApplicationManager() 