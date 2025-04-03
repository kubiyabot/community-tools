from typing import List
from .base import ArgoCDTool, ArgoCDGitTool, ArgoCDKubeTool, Arg
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
                self.deploy_application()
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

            # Check if application exists and get details
            echo "🔍 Checking application status..."
            if ! argocd app get "$app_name" --insecure &>/dev/null; then
                echo "❌ Application '$app_name' not found"
                exit 1
            fi

            # Get initial state and source details
            echo "📊 Initial application state:"
            app_info=$(argocd app get "$app_name" --insecure -o json)
            echo "$app_info" | jq '.'

            # Get source repo and path
            repo_url=$(echo "$app_info" | jq -r '.spec.source.repoURL')
            repo_path=$(echo "$app_info" | jq -r '.spec.source.path')
            echo "📁 Source: $repo_url -> $repo_path"

            # Clone and validate configuration
            echo "🔍 Validating application source..."
            temp_dir=$(mktemp -d)
            if ! git clone "$repo_url" "$temp_dir"; then
                echo "❌ Failed to clone repository"
                rm -rf "$temp_dir"
                exit 1
            fi

            cd "$temp_dir/$repo_path"
            
            echo "📁 Directory contents:"
            ls -la

            # Detect configuration type
            if [ -f "Chart.yaml" ]; then
                echo "📦 Detected Helm chart"
                echo "📋 Chart.yaml contents:"
                cat Chart.yaml
                
                echo "\n📋 Values.yaml contents (if exists):"
                if [ -f "values.yaml" ]; then
                    cat values.yaml
                else
                    echo "No values.yaml found"
                fi
                
                echo "\n🔍 Running helm lint..."
                helm lint .
                
                echo "\n🔍 Running helm template..."
                helm template . --debug

            elif [ -f "kustomization.yaml" ] || [ -f "kustomization.yml" ]; then
                echo "📦 Detected Kustomize configuration"
                echo "📋 Kustomization contents:"
                cat kustomization.ya?ml
                
                echo "\n🔍 Running kustomize build..."
                kustomize build .

            elif [ -f "values.yaml" ] || [ -f "values.yml" ]; then
                echo "📦 Detected values configuration"
                echo "📋 Values contents:"
                cat values.ya?ml
                
                echo "\n📁 Looking for associated manifests..."
                find . -type f -name "*.yaml" -o -name "*.yml" | while read -r file; do
                    if [ "$file" != "./values.yaml" ] && [ "$file" != "./values.yml" ]; then
                        echo "\n📄 Contents of $file:"
                        cat "$file"
                    fi
                done

            else
                echo "📦 Looking for Kubernetes manifests..."
                yaml_files=$(find . -type f -name "*.yaml" -o -name "*.yml")
                if [ -n "$yaml_files" ]; then
                    echo "Found YAML files:"
                    echo "$yaml_files"
                    echo "\n📋 Contents of YAML files:"
                    for file in $yaml_files; do
                        echo "\n📄 $file:"
                        cat "$file"
                    done
                else
                    echo "⚠️ No YAML files found in $repo_path"
                    echo "Directory contents:"
                    ls -la
                fi
            fi

            cd - > /dev/null
            rm -rf "$temp_dir"

            # Refresh application to ensure latest state
            echo "🔄 Refreshing application state..."
            argocd app refresh "$app_name" --insecure

            # Show current ArgoCD application configuration
            echo "📋 Current ArgoCD Application Configuration:"
            argocd app get "$app_name" --insecure
            
            # Try to get more details about what ArgoCD is doing
            echo "\n🔍 Checking ArgoCD controller logs..."
            kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=50 | grep -i "$app_name"
            
            # Check if ArgoCD can access the repo
            echo "\n🔍 Verifying repository access..."
            argocd repo get "$repo_url" --insecure || {
                echo "⚠️ Repository not registered with ArgoCD"
                echo "Attempting to register repository..."
                argocd repo add "$repo_url" --insecure
            }

            # Force a hard refresh of the application
            echo "\n🔄 Force refreshing application..."
            argocd app get "$app_name" --refresh --hard --insecure

            # Show what ArgoCD thinks it should deploy
            echo "\n📋 Expected resources to be created:"
            argocd app manifests "$app_name" --insecure || echo "No manifests generated"

            # Sync with more aggressive options
            echo "\n🔄 Syncing application with force..."
            if ! argocd app sync "$app_name" --force --prune --replace --insecure; then
                echo "❌ Failed to sync application"
                echo "📝 Sync error details:"
                argocd app get "$app_name" --insecure
                
                echo "\n📝 ArgoCD controller logs:"
                kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=100 | grep -i "$app_name"
                
                exit 1
            fi

            # Wait for sync to complete
            echo "⏳ Waiting for sync to complete..."
            timeout=300  # 5 minutes timeout
            elapsed=0
            while [ $elapsed -lt $timeout ]; do
                # Get full application state
                app_state=$(argocd app get "$app_name" --insecure -o json)
                
                # Extract status information
                status=$(echo "$app_state" | jq -r '.status.sync.status // "Unknown"')
                health=$(echo "$app_state" | jq -r '.status.health.status // "Unknown"')
                
                echo "📊 Current status: Sync=$status, Health=$health"
                
                if [ "$status" = "Synced" ] && [ "$health" = "Healthy" ]; then
                    echo "✅ Application deployed successfully!"
                    
                    # Show full application state for debugging
                    echo "📋 Full Application State:"
                    echo "$app_state" | jq '.'

                    # Show manifest details
                    echo "\n📄 Generated Manifests:"
                    argocd app manifests "$app_name" --insecure

                    # Show application resources
                    echo "\n📦 Application Resources:"
                    kubectl get all -n "$namespace"

                    # Show Kubernetes events
                    echo "\n📝 Recent Kubernetes events:"
                    kubectl get events --namespace "$namespace" --sort-by='.lastTimestamp'

                    # Check if any resources were actually created
                    if ! kubectl get all -n "$namespace" 2>/dev/null | grep -q .; then
                        echo "⚠️ Warning: No resources were created in the namespace"
                        echo "🔍 Debugging information:"
                        
                        echo "\n📝 ArgoCD Application Status:"
                        argocd app get "$app_name" --insecure
                        
                        echo "\n📝 ArgoCD Controller Logs:"
                        kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=100 | grep -i "$app_name"
                        
                        echo "\n📝 ArgoCD Repo Server Logs:"
                        kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=50
                        
                        echo "\n📝 Application Diff:"
                        argocd app diff "$app_name" --insecure
                        
                        echo "\n📝 Expected Manifests:"
                        argocd app manifests "$app_name" --insecure || echo "No manifests generated"
                        
                        exit 1
                    fi

                    exit 0
                fi
                
                if [ "$status" = "OutOfSync" ] || [ "$health" = "Degraded" ]; then
                    echo "⚠️ Application is in a degraded state"
                    echo "📝 Application Events:"
                    argocd app history "$app_name" --insecure
                    echo "\n📝 Recent Kubernetes events:"
                    kubectl get events --namespace "$namespace" --sort-by='.lastTimestamp'
                    echo "\n🔍 Application Diff:"
                    argocd app diff "$app_name" --insecure
                    exit 1
                fi
                
                sleep 10
                elapsed=$((elapsed + 10))
            done

            echo "❌ Deployment timed out after ${timeout}s"
            echo "📝 Final Application State:"
            argocd app get "$app_name" --insecure
            echo "\n📝 Recent events:"
            kubectl get events --namespace "$namespace" --sort-by='.lastTimestamp'
            echo "\n🔍 Application Diff:"
            argocd app diff "$app_name" --insecure
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



# Initialize when module is imported
ApplicationManager() 