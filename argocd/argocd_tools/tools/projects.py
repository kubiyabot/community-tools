from typing import List
import sys
from .base import ArgoCDTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class ProjectTools:
    """ArgoCD project management tools."""

    def __init__(self):
        """Initialize and register all ArgoCD project tools."""
        try:
            tools = [
                self.list_projects(),
                self.get_project_details(),
                self.create_project(),
                self.delete_project()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD project tools: {str(e)}", file=sys.stderr)
            raise

    def list_projects(self) -> ArgoCDTool:
        """List all ArgoCD projects."""
        return ArgoCDTool(
            name="argocd_list_projects",
            description="List all projects in ArgoCD",
            content="""
            apk add --no-cache -q jq curl

            echo "=== ArgoCD Projects ==="
            
            # Fetch projects
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/projects")
            
            # Parse and display projects
            echo "Attempting to parse projects..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq -r '.items[] | {
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations
            }' | jq -s '.' 2>/dev/null); then
                echo "Failed to parse projects. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )
        
    def get_project_details(self) -> ArgoCDTool:
        """Get detailed information about a specific ArgoCD project."""
        return ArgoCDTool(
            name="argocd_project_details",
            description="Get detailed information about a specific ArgoCD project",
            content="""
            apk add --no-cache -q jq curl

            # Validate required parameters
            if [ -z "$project_name" ]; then
                echo "Error: Project name is required"
                exit 1
            fi
            
            echo "=== Project Details: $project_name ==="
            
            # Fetch project details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/projects/$project_name")
            
            # Parse and display project details
            echo "Attempting to parse project details..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations,
                cluster_resource_whitelist: .spec.clusterResourceWhitelist,
                namespace_resource_blacklist: .spec.namespaceResourceBlacklist,
                roles: .spec.roles
            }' 2>/dev/null); then
                echo "Failed to parse project details. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            
            # Get applications in project
            echo "=== Applications in Project ==="
            APPS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications?project=$project_name")
            
            # Parse and display applications
            echo "Attempting to parse applications..."
            if ! PARSED_APPS=$(echo "$APPS_RESPONSE" | jq -r '.items[] | {
                name: .metadata.name,
                sync_status: .status.sync.status,
                health_status: .status.health.status
            }' | jq -s '.' 2>/dev/null); then
                echo "Failed to parse applications. Raw response:"
                echo "$APPS_RESPONSE"
            else
                echo "$PARSED_APPS"
            fi
            """,
            args=[Arg(name="project_name", description="Name of the ArgoCD project", required=True)],
            image="curlimages/curl:8.1.2"
        )
        
    def create_project(self) -> ArgoCDTool:
        """Create a new ArgoCD project."""
        return ArgoCDTool(
            name="argocd_create_project",
            description="Create a new ArgoCD project with specified settings",
            content="""
            apk add --no-cache -q jq curl
            
            # Validate required parameters
            if [ -z "$project_name" ]; then
                echo "Error: Project name is required"
                exit 1
            fi

            # Set default values for optional parameters
            DESCRIPTION="${description:-}"
            SOURCE_REPOS="${source_repos:-*}"
            DESTINATIONS="${destinations:-*,*}"
            
            echo "=== Creating Project: $project_name ==="
            
            # Prepare destinations JSON
            DEST_JSON=""
            IFS=','
            for dest in $DESTINATIONS; do
                SERVER="${dest%:*}"
                NAMESPACE="${dest#*:}"
                if [ "$SERVER" = "$NAMESPACE" ]; then NAMESPACE="*"; fi
                DEST_JSON="$DEST_JSON{\"server\": \"$SERVER\", \"namespace\": \"$NAMESPACE\"},"
            done
            DEST_JSON=$(echo "$DEST_JSON" | sed 's/,$//')
            
            # Prepare source repos JSON
            REPOS_JSON=""
            for repo in ${SOURCE_REPOS//,/ }; do
                REPOS_JSON="$REPOS_JSON\"$repo\","
            done
            REPOS_JSON=$(echo "$REPOS_JSON" | sed 's/,$//')
            
            # Create project
            RESPONSE=$(curl -s -k -X POST \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{
                    "metadata": {
                        "name": "'"$project_name"'"
                    },
                    "spec": {
                        "description": "'"$DESCRIPTION"'",
                        "sourceRepos": ['"$REPOS_JSON"'],
                        "destinations": ['"$DEST_JSON"']
                    }
                }' \
                "$ARGOCD_DOMAIN/api/v1/projects")
            
            # Parse and display response
            echo "Attempting to parse response..."
            if ! PARSED_RESPONSE=$(echo "$RESPONSE" | jq '{
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations
            }' 2>/dev/null); then
                echo "Failed to parse response. Raw response:"
                echo "$RESPONSE"
            else
                echo "$PARSED_RESPONSE"
            fi
            """,
            args=[
                Arg(name="project_name", description="Name of the ArgoCD project", required=True),
                Arg(name="description", description="Description of the project", required=False),
                Arg(name="source_repos", description="Allowed source repositories (comma-separated list, use '*' for all)", required=False),
                Arg(name="destinations", description="Allowed destination clusters/namespaces (format: server:namespace,server:namespace)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def delete_project(self) -> ArgoCDTool:
        """Delete an ArgoCD project."""
        return ArgoCDTool(
            name="argocd_delete_project",
            description="Delete an ArgoCD project",
            content="""
            apk add --no-cache -q jq curl
            
            # Validate required parameters
            if [ -z "$project_name" ]; then
                echo "Error: Project name is required"
                exit 1
            fi

            echo "=== Deleting Project: $project_name ==="
            
            # Check if project has applications
            echo "Checking for applications in project..."
            APPS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_TOKEN" "$ARGOCD_DOMAIN/api/v1/applications?project=$project_name")
            
            # Parse applications response
            if ! APPS_COUNT=$(echo "$APPS_RESPONSE" | jq '.items | length' 2>/dev/null); then
                echo "Failed to check for applications. Raw response:"
                echo "$APPS_RESPONSE"
                return 1
            fi
            
            if [ "$APPS_COUNT" -gt 0 ] && [ "$force" != "true" ]; then
                echo "Project has $APPS_COUNT applications. Use force=true to delete anyway."
                echo "Attempting to list applications..."
                if ! APP_NAMES=$(echo "$APPS_RESPONSE" | jq -r '.items[].metadata.name' 2>/dev/null); then
                    echo "Failed to list applications. Raw response:"
                    echo "$APPS_RESPONSE"
                else
                    echo "Applications in project:"
                    echo "$APP_NAMES"
                fi
                return 1
            elif [ "$APPS_COUNT" -gt 0 ]; then
                echo "Warning: Deleting project with $APPS_COUNT applications because force=true"
            fi
            
            # Delete project
            RESPONSE=$(curl -s -k -X DELETE \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "$ARGOCD_DOMAIN/api/v1/projects/$project_name")
            
            # Parse and display response
            echo "Attempting to parse response..."
            if ! ERROR_CHECK=$(echo "$RESPONSE" | jq -r '.code // 0' 2>/dev/null); then
                echo "Failed to parse response. Raw response:"
                echo "$RESPONSE"
            elif [ "$ERROR_CHECK" -ne 0 ]; then
                echo "Error: $(echo "$RESPONSE" | jq -r '.message')"
            else
                echo "Project deleted successfully: $project_name"
            fi
            """,
            args=[
                Arg(name="project_name", description="Name of the ArgoCD project", required=True),
                Arg(name="force", description="Force deletion even if project has applications", required=False)
            ],
            image="curlimages/curl:8.1.2"
        ) 

ProjectTools()