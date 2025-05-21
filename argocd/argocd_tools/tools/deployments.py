from typing import List
import sys
from .base import ArgoCDTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class DeploymentTools:
    """ArgoCD deployment management tools."""

    def __init__(self):
        """Initialize and register all ArgoCD deployment tools."""
        try:
            tools = [
                self.list_deployments(),
                self.get_deployment_details(),
                self.get_deployment_sync_status(),
                self.get_deployment_manifest(),
                self.get_deployment_logs()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD deployment tools: {str(e)}", file=sys.stderr)
            raise

    def list_deployments(self) -> ArgoCDTool:
        """List all deployments across all ArgoCD applications or within a specific application."""
        return ArgoCDTool(
            name="argocd_list_deployments",
            description="List all Deployment resources across ArgoCD applications",
            content="""
            apk add --no-cache -q jq curl

            # Set default values for optional parameters
            APP_NAME=${app_name:-""}
            
            echo "=== ArgoCD Deployments ==="
            
            if [ -z "$APP_NAME" ]; then
                # Get all applications first
                APPS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications")
                
                echo "Searching for deployments across all applications..."
                
                # Create an empty array to store deployments
                DEPLOYMENTS="[]"
                
                # Iterate through each application to get its deployments
                for APP in $(echo "$APPS_RESPONSE" | jq -r '.items[].metadata.name'); do
                    echo "Checking application: $APP"
                    
                    # Get resource tree for this application
                    TREE_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$APP/resource-tree")
                    
                    # Extract deployments and add application name
                    APP_DEPLOYMENTS=$(echo "$TREE_RESPONSE" | jq -c '[.nodes[] | select(.kind == "Deployment") | {
                        app: "'"$APP"'",
                        name: .name,
                        namespace: .namespace,
                        group: .group,
                        version: .version,
                        sync_status: .syncStatus,
                        health_status: .health.status
                    }]')
                    
                    # Combine with existing deployments
                    DEPLOYMENTS=$(echo "$DEPLOYMENTS" "$APP_DEPLOYMENTS" | jq -s 'add')
                done
                
                # Display results
                echo "$DEPLOYMENTS"
            else
                # Get deployments for a specific application
                echo "Searching for deployments in application: $APP_NAME"
                
                # Get resource tree for this application
                TREE_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$APP_NAME/resource-tree")
                
                # Extract deployments
                DEPLOYMENTS=$(echo "$TREE_RESPONSE" | jq '[.nodes[] | select(.kind == "Deployment") | {
                    app: "'"$APP_NAME"'",
                    name: .name,
                    namespace: .namespace,
                    group: .group,
                    version: .version,
                    sync_status: .syncStatus,
                    health_status: .health.status
                }]')
                
                # Display results
                echo "$DEPLOYMENTS"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application (optional)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_deployment_details(self) -> ArgoCDTool:
        """Get detailed information about a specific Deployment."""
        return ArgoCDTool(
            name="argocd_deployment_details",
            description="Get detailed information about a specific Deployment",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$deployment_name" ] || [ -z "$namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, deployment_name, namespace"
                exit 1
            fi
            
            echo "=== Deployment Details: $deployment_name in $namespace ==="
            
            # Fetch deployment details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource?resourceName=$deployment_name&namespace=$namespace&kind=Deployment&group=apps&version=v1")
            
            # Parse and display deployment details
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                name: .metadata.name,
                namespace: .metadata.namespace,
                replicas: .spec.replicas,
                strategy: .spec.strategy.type,
                selector: .spec.selector,
                containers: [.spec.template.spec.containers[] | {
                    name: .name,
                    image: .image,
                    resources: .resources
                }],
                status: {
                    replicas: .status.replicas,
                    available_replicas: .status.availableReplicas,
                    ready_replicas: .status.readyReplicas,
                    updated_replicas: .status.updatedReplicas
                }
            }' 2>/dev/null); then
                echo "Failed to parse deployment details. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            
            # Get replicasets for this deployment
            echo "=== ReplicaSets for Deployment ==="
            TREE_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource-tree")
            
            # Find ReplicaSets that belong to this deployment
            REPLICASETS=$(echo "$TREE_RESPONSE" | jq -r '[.nodes[] | select(.kind == "ReplicaSet" and .parentRefs[].name == "'"$deployment_name"'") | {
                name: .name,
                generation: .info[].value,
                revision: .info[1].value,
                status: .health.status,
                pods: .info[2].value
            }]')
            
            echo "$REPLICASETS"
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="deployment_name", description="Name of the Deployment", required=True),
                Arg(name="namespace", description="Namespace of the Deployment", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_deployment_sync_status(self) -> ArgoCDTool:
        """Get the sync status of a specific Deployment."""
        return ArgoCDTool(
            name="argocd_deployment_sync_status",
            description="Get the synchronization status of a Deployment resource",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$deployment_name" ] || [ -z "$namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, deployment_name, namespace"
                exit 1
            fi
            
            echo "=== Sync Status for Deployment: $deployment_name in $namespace ==="
            
            # Fetch application resource tree
            TREE_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource-tree")
            
            # Find the deployment in the resource tree
            DEPLOYMENT_STATUS=$(echo "$TREE_RESPONSE" | jq '.nodes[] | select(.kind == "Deployment" and .name == "'"$deployment_name"'" and .namespace == "'"$namespace"'") | {
                name: .name,
                namespace: .namespace,
                sync_status: .syncStatus,
                health_status: .health.status,
                hook_status: .hookStatus,
                hook_type: .hookType,
                created_at: .createdAt
            }')
            
            if [ -z "$DEPLOYMENT_STATUS" ]; then
                echo "Deployment not found in application resource tree"
            else
                echo "$DEPLOYMENT_STATUS"
            fi
            
            # Get comparison results to see if there are any differences
            echo "=== Comparison with Git source ==="
            COMPARISON_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name")
            
            # Extract resources with differences
            DIFF_RESOURCES=$(echo "$COMPARISON_RESPONSE" | jq '.status.resources[] | select(.kind == "Deployment" and .name == "'"$deployment_name"'" and .namespace == "'"$namespace"'")')
            
            if [ -z "$DIFF_RESOURCES" ]; then
                echo "No sync differences found for this deployment"
            else
                echo "$DIFF_RESOURCES"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="deployment_name", description="Name of the Deployment", required=True),
                Arg(name="namespace", description="Namespace of the Deployment", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_deployment_manifest(self) -> ArgoCDTool:
        """Get the full manifest of a specific Deployment."""
        return ArgoCDTool(
            name="argocd_deployment_manifest",
            description="Get the full YAML manifest of a Deployment resource",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$deployment_name" ] || [ -z "$namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, deployment_name, namespace"
                exit 1
            fi
            
            # Set default values for optional parameters
            FORMAT=${format:-"json"}
            
            echo "=== Manifest for Deployment: $deployment_name in $namespace ==="
            
            # Fetch deployment manifest - using resourceName as required by the API
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource?resourceName=$deployment_name&namespace=$namespace&kind=Deployment&group=apps&version=v1")
            
            # Check for API errors
            if echo "$RESPONSE" | grep -q "error"; then
                echo "API Error occurred:"
                echo "$RESPONSE"
                
                # Try alternative API endpoint as fallback
                echo "Trying alternative endpoint..."
                RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    "$ARGOCD_DOMAIN/api/v1/applications/$app_name/manifests?revision=&all=true" | \
                    jq --arg name "$deployment_name" '.manifests[] | select(.metadata.name == $name and .kind == "Deployment")')
            fi
            
            # Output in requested format
            if [ "$FORMAT" = "yaml" ]; then
                # Install yq for YAML conversion if needed
                apk add --no-cache -q yq
                
                # Convert to YAML and display
                echo "$RESPONSE" | yq -P
            else
                # Display as formatted JSON
                echo "$RESPONSE" | jq '.'
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="deployment_name", description="Name of the Deployment", required=True),
                Arg(name="namespace", description="Namespace of the Deployment", required=True),
                Arg(name="format", description="Output format: json or yaml (default: json)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_deployment_logs(self) -> ArgoCDTool:
        """Get logs from a specific Deployment."""
        return ArgoCDTool(
            name="argocd_deployment_logs",
            description="Get logs from a Deployment resource",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$deployment_name" ] || [ -z "$namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, deployment_name, namespace"
                exit 1
            fi
            
            # Set default values for optional parameters
            TAIL_LINES=${tail_lines:-1000}
            
            echo "=== Logs for Deployment: $deployment_name in $namespace ==="
            
            # Build query parameters for the direct logs endpoint
            QUERY="appNamespace=$namespace&namespace=$namespace&follow=false&group=apps&kind=Deployment&resourceName=$deployment_name&tailLines=$TAIL_LINES&sinceSeconds=0"
            
            # Fetch logs using the direct deployment logs endpoint
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/logs?$QUERY")
            
            # Parse into a cleaner format with timestamp, content and pod
            echo "$RESPONSE" | jq -r '
                if type == "array" then
                    .[]
                else
                    .
                end |
                if has("result") then
                    "[\(.result.timeStampStr)] [\(.result.podName)] \(.result.content)"
                elif has("content") then
                    "[\(.timeStampStr)] [\(.podName)] \(.content)"
                else
                    .
                end
            ' 2>/dev/null || echo "$RESPONSE"
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="deployment_name", description="Name of the Deployment", required=True),
                Arg(name="namespace", description="Namespace of the Deployment", required=True),
                Arg(name="tail_lines", description="Number of lines to show from the end (default: 1000)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

DeploymentTools() 