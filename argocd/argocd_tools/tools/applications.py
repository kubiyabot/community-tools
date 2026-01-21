from typing import List
import sys
from .base import ArgoCDTool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry

class ApplicationTools:
    """ArgoCD application management tools."""

    def __init__(self):
        """Initialize and register all ArgoCD application tools."""
        try:
            tools = [
                self.list_applications(),
                self.get_application_details(),
                self.sync_application(),
                self.get_sync_status(),
                self.create_application(),
                self.delete_application()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD application tools: {str(e)}", file=sys.stderr)
            raise

    def list_applications(self) -> ArgoCDTool:
        """List all ArgoCD applications."""
        return ArgoCDTool(
            name="argocd_list_applications",
            description="List all applications managed by ArgoCD",
            content="""
            apk add --no-cache -q jq curl

            echo "=== ArgoCD Applications ==="
            
            # Fetch applications
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications")
            
            # Parse and display applications
            echo "Attempting to parse applications..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq -r '.items[] | {
                name: .metadata.name,
                project: .spec.project,
                sync_status: .status.sync.status,
                health_status: .status.health.status,
                repo: .spec.source.repoURL,
                path: .spec.source.path,
                target_revision: .spec.source.targetRevision,
                destination: "\(.spec.destination.server)/\(.spec.destination.namespace)"
            }' | jq -s '.' 2>/dev/null); then
                echo "Failed to parse applications. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )
        
    def get_application_details(self) -> ArgoCDTool:
        """Get detailed information about a specific ArgoCD application."""
        return ArgoCDTool(
            name="argocd_application_details",
            description="Get detailed information about a specific ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ]; then
                echo "Error: Application name is required"
                exit 1
            fi
            
            echo "=== Application Details: $app_name ==="
            
            # Fetch application details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name")
            
            # Parse and display application details
            echo "Attempting to parse application details..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                name: .metadata.name,
                project: .spec.project,
                sync_status: .status.sync.status,
                health_status: .status.health.status,
                repo: .spec.source.repoURL,
                path: .spec.source.path,
                target_revision: .spec.source.targetRevision,
                destination: {
                    server: .spec.destination.server,
                    namespace: .spec.destination.namespace
                },
                auto_sync: .spec.syncPolicy.automated,
                created_at: .metadata.creationTimestamp
            }' 2>/dev/null); then
                echo "Failed to parse application details. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[Arg(name="app_name", description="Name of the ArgoCD application", required=True)],
            image="curlimages/curl:8.1.2"
        )
        
    def sync_application(self) -> ArgoCDTool:
        """Synchronize an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_sync_application",
            description="Synchronize an ArgoCD application with its source repository",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ]; then
                echo "Error: Application name is required"
                exit 1
            fi
            
            echo "=== Syncing Application: $app_name ==="
            
            # Set default values for optional parameters
            PRUNE=${prune:-false}
            REPLACE=${replace:-false}
            FORCE=${force:-false}
            
            # Construct sync options
            SYNC_OPTIONS="--prune=$PRUNE --replace=$REPLACE --force=$FORCE"
            if [ -n "$resources" ]; then
                SYNC_OPTIONS="$SYNC_OPTIONS --resource=$resources"
            fi
            
            # Trigger sync
            RESPONSE=$(curl -s -k -X POST \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{
                    "prune": '"$PRUNE"',
                    "dryRun": false,
                    "replace": '"$REPLACE"',
                    "force": '"$FORCE"'
                }' \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/sync")
            
            # Parse and display response
            echo "Attempting to parse sync result..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                revision: .operationState.syncResult.revision,
                phase: .operationState.phase,
                message: .operationState.message
            }' 2>/dev/null); then
                echo "Failed to parse sync result. Raw response:"
                echo "$RESPONSE"
            else
                echo "Sync initiated for application: $app_name"
                echo "Sync details:"
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="prune", description="Prune resources that are no longer defined in Git", required=False),
                Arg(name="replace", description="Replace resources instead of applying changes", required=False),
                Arg(name="force", description="Force sync even if the application is already synced", required=False),
                Arg(name="resources", description="Specific resources to sync (format: group:kind:name)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_sync_status(self) -> ArgoCDTool:
        """Get the sync status of a specific ArgoCD application."""
        return ArgoCDTool(
            name="argocd_sync_status",
            description="Get the synchronization status of an ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ]; then
                echo "Error: Application name is required"
                exit 1
            fi
            
            echo "=== Sync Status: $app_name ==="
            
            # Fetch application details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name")
            
            # Get sync status and health status
            echo "Attempting to parse application status..."
            if ! SYNC_STATUS=$(echo "$RESPONSE" | jq '.status.sync' 2>/dev/null); then
                echo "Failed to parse sync status. Raw response:"
                echo "$RESPONSE"
                exit 1
            fi
            
            if ! HEALTH_STATUS=$(echo "$RESPONSE" | jq '.status.health' 2>/dev/null); then
                echo "Failed to parse health status. Raw response:"
                echo "$RESPONSE"
                exit 1
            fi
            
            echo "Application: $app_name"
            echo "Sync status: $(echo "$SYNC_STATUS" | jq -r '.status')"
            echo "To revision: $(echo "$SYNC_STATUS" | jq -r '.revision')"
            echo "Health status: $(echo "$HEALTH_STATUS" | jq -r '.status')"
            
            # Get detailed resource tree
            RESOURCE_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource-tree")
            
            # Parse and display resource status
            echo "Attempting to parse resource status..."
            if ! PARSED_RESOURCES=$(echo "$RESOURCE_RESPONSE" | jq '.nodes[] | {
                kind: .kind,
                name: .name,
                namespace: .namespace,
                health: .health.status,
                status: .syncStatus,
                message: .health.message
            }' | jq -s '.' 2>/dev/null); then
                echo "Failed to parse resource status. Raw response:"
                echo "$RESOURCE_RESPONSE"
            else
                echo "Resource status:"
                echo "$PARSED_RESOURCES"
            fi
            """,
            args=[Arg(name="app_name", description="Name of the ArgoCD application", required=True)],
            image="curlimages/curl:8.1.2"
        )
        
    def create_application(self) -> ArgoCDTool:
        """Create a new ArgoCD application."""
        return ArgoCDTool(
            name="argocd_create_application",
            description="Create a new ArgoCD application from a Git repository",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$repo_url" ] || [ -z "$path" ] || [ -z "$dest_namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, repo_url, path, dest_namespace"
                exit 1
            fi
            
            # Set default values for optional parameters
            PROJECT=${project:-default}
            TARGET_REVISION=${target_revision:-HEAD}
            DEST_SERVER=${dest_server:-https://kubernetes.default.svc}
            AUTO_SYNC=${auto_sync:-false}
            PRUNE=${prune:-false}
            SELF_HEAL=${self_heal:-false}
            
            # Prepare sync policy JSON
            if [ "$AUTO_SYNC" = "true" ]; then
                SYNC_POLICY='{
                    "automated": {
                        "prune": '"$PRUNE"',
                        "selfHeal": '"$SELF_HEAL"'
                    }
                }'
            else
                SYNC_POLICY='null'
            fi
            
            echo "=== Creating Application: $app_name ==="
            
            # Create application
            RESPONSE=$(curl -s -k -X POST \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{
                    "metadata": {
                        "name": "'"$app_name"'"
                    },
                    "spec": {
                        "project": "'"$PROJECT"'",
                        "source": {
                            "repoURL": "'"$repo_url"'",
                            "path": "'"$path"'",
                            "targetRevision": "'"$TARGET_REVISION"'"
                        },
                        "destination": {
                            "server": "'"$DEST_SERVER"'",
                            "namespace": "'"$dest_namespace"'"
                        },
                        "syncPolicy": '"$SYNC_POLICY"'
                    }
                }' \
                "$ARGOCD_DOMAIN/api/v1/applications")
            
            # Parse and display response
            echo "Attempting to parse response..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                name: .metadata.name,
                project: .spec.project,
                repo: .spec.source.repoURL,
                path: .spec.source.path,
                destination: {
                    server: .spec.destination.server,
                    namespace: .spec.destination.namespace
                },
                auto_sync: .spec.syncPolicy.automated
            }' 2>/dev/null); then
                echo "Failed to parse response. Raw response:"
                echo "$RESPONSE"
            else
                echo "Application created successfully:"
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="repo_url", description="URL of the Git repository", required=True),
                Arg(name="path", description="Path within the repository to the application manifests", required=True),
                Arg(name="dest_namespace", description="Target namespace for the application", required=True),
                Arg(name="project", description="ArgoCD project name", required=False),
                Arg(name="target_revision", description="Target revision for the application (branch, tag, commit)", required=False),
                Arg(name="dest_server", description="Destination Kubernetes API server URL", required=False),
                Arg(name="auto_sync", description="Enable automatic synchronization", required=False),
                Arg(name="prune", description="Automatically prune resources", required=False),
                Arg(name="self_heal", description="Automatically self-heal out-of-sync resources", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def delete_application(self) -> ArgoCDTool:
        """Delete an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_delete_application",
            description="Delete an ArgoCD application and optionally its resources",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ]; then
                echo "Error: Application name is required"
                exit 1
            fi
            
            # Set default values for optional parameters
            CASCADE=${cascade:-true}
            PROPAGATION_POLICY=${propagation_policy:-foreground}
            
            echo "=== Deleting Application: $app_name ==="
            
            # Delete application
            RESPONSE=$(curl -s -k -X DELETE \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name?cascade=$CASCADE&propagationPolicy=$PROPAGATION_POLICY")
            
            # Parse and display response
            echo "Attempting to parse response..."
            if ! ERROR_CHECK=$(echo "$RESPONSE" | jq -r '.code // 0' 2>/dev/null); then
                echo "Failed to parse response. Raw response:"
                echo "$RESPONSE"
            elif [ "$ERROR_CHECK" -ne 0 ]; then
                echo "Error: $(echo "$RESPONSE" | jq -r '.message')"
            else
                echo "Application deletion initiated: $app_name"
                if [ "$CASCADE" = "true" ]; then
                    echo "All application resources will be deleted"
                else
                    echo "Application will be removed from ArgoCD but resources will remain in the cluster"
                fi
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="cascade", description="Delete application resources as well as the application", required=False),
                Arg(name="propagation_policy", description="Propagation policy for resource deletion (foreground or background)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        ) 

ApplicationTools()