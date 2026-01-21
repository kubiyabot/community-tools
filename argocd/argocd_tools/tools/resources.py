from typing import List
import sys
from .base import ArgoCDTool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry

class ResourceTools:
    """ArgoCD resource management tools."""

    def __init__(self):
        """Initialize and register all ArgoCD resource tools."""
        try:
            tools = [
                self.list_resources(),
                self.get_resource_details(),
                self.get_resource_logs(),
                self.get_resource_events()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD resource tools: {str(e)}", file=sys.stderr)
            raise

    def list_resources(self) -> ArgoCDTool:
        """List all resources within an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_list_resources",
            description="List all resources deployed by an ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ]; then
                echo "Error: Application name is required"
                exit 1
            fi
            
            echo "=== Resources for Application: $app_name ==="
            
            # Fetch resource tree
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource-tree")
            
            # Parse and display resources
            echo "Attempting to parse resource tree..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '.nodes[] | {
                kind: .kind,
                group: .group,
                name: .name,
                namespace: .namespace,
                version: .version,
                sync_status: .syncStatus,
                health_status: .health.status
            }' | jq -s '.' 2>/dev/null); then
                echo "Failed to parse resource tree. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_resource_details(self) -> ArgoCDTool:
        """Get detailed information about a specific resource in an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_resource_details",
            description="Get detailed information about a specific resource in an ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$resource_name" ] || [ -z "$resource_kind" ] || [ -z "$resource_namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, resource_name, resource_kind, resource_namespace"
                exit 1
            fi
            
            # Set default values for optional parameters
            RESOURCE_GROUP=${resource_group:-""}
            RESOURCE_VERSION=${resource_version:-""}
            
            echo "=== Resource Details: $resource_kind/$resource_name in $resource_namespace ==="
            
            # Fetch resource details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource?name=$resource_name&namespace=$resource_namespace&kind=$resource_kind&group=$RESOURCE_GROUP&version=$RESOURCE_VERSION")
            
            # Parse and display resource details
            echo "Attempting to parse resource details..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '.' 2>/dev/null); then
                echo "Failed to parse resource details. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            
            # Get available actions for this resource
            echo "=== Available Actions ==="
            ACTIONS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/resource/actions?name=$resource_name&namespace=$resource_namespace&kind=$resource_kind&group=$RESOURCE_GROUP&version=$RESOURCE_VERSION")
            
            # Parse and display actions
            if ! ACTIONS=$(echo "$ACTIONS_RESPONSE" | jq '.' 2>/dev/null); then
                echo "Failed to parse resource actions. Raw response:"
                echo "$ACTIONS_RESPONSE"
            else
                echo "$ACTIONS"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="resource_name", description="Name of the resource", required=True),
                Arg(name="resource_kind", description="Kind of the resource (e.g., Deployment, Service)", required=True),
                Arg(name="resource_namespace", description="Namespace of the resource", required=True),
                Arg(name="resource_group", description="API Group of the resource (e.g., apps, networking.k8s.io)", required=False),
                Arg(name="resource_version", description="Version of the resource", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_resource_logs(self) -> ArgoCDTool:
        """Get logs for a Pod resource in an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_resource_logs",
            description="Get logs for a Pod resource in an ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$pod_name" ] || [ -z "$namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, pod_name, namespace"
                exit 1
            fi
            
            # Set default values for optional parameters
            CONTAINER=${container:-""}
            TAIL_LINES=${tail_lines:-100}
            FOLLOW=${follow:-false}
            
            echo "=== Logs for Pod: $pod_name in $namespace ==="
            
            # Build query parameters
            QUERY="podName=$pod_name&namespace=$namespace&tailLines=$TAIL_LINES"
            if [ -n "$CONTAINER" ]; then
                QUERY="$QUERY&container=$CONTAINER"
            fi
            
            # Fetch logs
            if [ "$FOLLOW" = "true" ]; then
                echo "Streaming logs (press Ctrl+C to stop)..."
                curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    "$ARGOCD_DOMAIN/api/v1/applications/$app_name/pods/$pod_name/logs?$QUERY"
            else
                RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    "$ARGOCD_DOMAIN/api/v1/applications/$app_name/pods/$pod_name/logs?$QUERY")
                echo "$RESPONSE"
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="pod_name", description="Name of the Pod", required=True),
                Arg(name="namespace", description="Namespace of the Pod", required=True),
                Arg(name="container", description="Container name (if Pod has multiple containers)", required=False),
                Arg(name="tail_lines", description="Number of lines to show from the end", required=False),
                Arg(name="follow", description="Stream logs in real-time", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def get_resource_events(self) -> ArgoCDTool:
        """Get Kubernetes events related to a resource in an ArgoCD application."""
        return ArgoCDTool(
            name="argocd_resource_events",
            description="Get Kubernetes events related to a resource in an ArgoCD application",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$app_name" ] || [ -z "$resource_name" ] || [ -z "$resource_namespace" ]; then
                echo "Error: Missing required parameters"
                echo "Required: app_name, resource_name, resource_namespace"
                exit 1
            fi
            
            echo "=== Events for Resource: $resource_name in $resource_namespace ==="
            
            # Fetch application details to get the destination server
            APP_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name")
            
            # Get events for the resource
            EVENTS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/applications/$app_name/events?resourceName=$resource_name&resourceNamespace=$resource_namespace")
            
            # Check if items exists and is not null in response
            ITEMS_COUNT=$(echo "$EVENTS_RESPONSE" | jq '.items | length // 0')
            
            if [ "$ITEMS_COUNT" = "0" ]; then
                echo "No events found for this resource."
                exit 0
            fi
            
            # Parse and display events
            echo "Found $ITEMS_COUNT events. Parsing..."
            PARSED_EVENTS=$(echo "$EVENTS_RESPONSE" | jq '.items[] | {
                type: .type,
                reason: .reason,
                message: .message,
                firstTimestamp: .firstTimestamp,
                lastTimestamp: .lastTimestamp,
                count: .count,
                involvedObject: .involvedObject
            }' | jq -s '.')
            
            echo "$PARSED_EVENTS"
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="resource_name", description="Name of the resource", required=True),
                Arg(name="resource_namespace", description="Namespace of the resource", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

ResourceTools() 