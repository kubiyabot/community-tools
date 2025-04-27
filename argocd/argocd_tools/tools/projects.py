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
            apk add --no-cache jq curl
            validate_argocd_connection

            echo "=== ArgoCD Projects ==="
            
            # Fetch projects
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" "$ARGOCD_SERVER/api/v1/projects")
            
            if [ -z "$RESPONSE" ]; then
                echo "Error: Failed to retrieve projects"
                exit 1
            fi
            
            # Parse and display projects
            echo "$RESPONSE" | jq -r '.items[] | {
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations
            }' | jq -s '.'
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
            apk add --no-cache jq curl
            validate_argocd_connection
            
            if [ -z "$project_name" ]; then
                echo "Error: Project name is required"
                exit 1
            fi
            
            echo "=== Project Details: $project_name ==="
            
            # Fetch project details
            RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" "$ARGOCD_SERVER/api/v1/projects/$project_name")
            
            if [ -z "$RESPONSE" ]; then
                echo "Error: Failed to retrieve project details"
                exit 1
            fi
            
            # Check if project exists
            ERROR_CODE=$(echo "$RESPONSE" | jq -r '.code // 0')
            if [ "$ERROR_CODE" -ne 0 ]; then
                echo "Error: $(echo "$RESPONSE" | jq -r '.message')"
                exit 1
            fi
            
            # Parse and display project details
            echo "$RESPONSE" | jq '{
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations,
                cluster_resource_whitelist: .spec.clusterResourceWhitelist,
                namespace_resource_blacklist: .spec.namespaceResourceBlacklist,
                roles: .spec.roles
            }'
            
            # Get applications in project
            echo "=== Applications in Project ==="
            APPS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" "$ARGOCD_SERVER/api/v1/applications?project=$project_name")
            
            if [ -z "$APPS_RESPONSE" ]; then
                echo "Error: Failed to retrieve applications in project"
                exit 1
            fi
            
            # Parse and display applications
            echo "$APPS_RESPONSE" | jq -r '.items[] | {
                name: .metadata.name,
                sync_status: .status.sync.status,
                health_status: .status.health.status
            }' | jq -s '.'
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
            apk add --no-cache jq curl
            validate_argocd_connection
            
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
            
            # Create project
            RESPONSE=$(curl -s -k -X POST \
                -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{
                    "metadata": {
                        "name": "'"$project_name"'"
                    },
                    "spec": {
                        "description": "'"$DESCRIPTION"'",
                        "sourceRepos": ["'"${SOURCE_REPOS//,/\",\"}"'"],
                        "destinations": [
                            '"$(IFS=,; for dest in $DESTINATIONS; do
                                SERVER="${dest%:*}"
                                NAMESPACE="${dest#*:}"
                                if [ "$SERVER" = "$NAMESPACE" ]; then NAMESPACE="*"; fi
                                echo "{\"server\": \"$SERVER\", \"namespace\": \"$NAMESPACE\"},"
                            done | sed 's/,$//')"'
                        ]
                    }
                }' \
                "$ARGOCD_SERVER/api/v1/projects")
            
            if [ -z "$RESPONSE" ]; then
                echo "Error: Failed to create project"
                exit 1
            fi
            
            # Check for errors
            ERROR_CODE=$(echo "$RESPONSE" | jq -r '.code // 0')
            if [ "$ERROR_CODE" -ne 0 ]; then
                echo "Error: $(echo "$RESPONSE" | jq -r '.message')"
                exit 1
            fi
            
            echo "Project created successfully:"
            echo "$RESPONSE" | jq '{
                name: .metadata.name,
                description: .spec.description,
                source_repos: .spec.sourceRepos,
                destinations: .spec.destinations
            }'
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
            apk add --no-cache jq curl
            validate_argocd_connection
            
            if [ -z "$project_name" ]; then
                echo "Error: Project name is required"
                exit 1
            fi
            
            # Check if project has applications
            echo "=== Checking Project Applications ==="
            APPS_RESPONSE=$(curl -s -k -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" "$ARGOCD_SERVER/api/v1/applications?project=$project_name")
            APPS_COUNT=$(echo "$APPS_RESPONSE" | jq '.items | length')
            
            if [ "$APPS_COUNT" -gt 0 ]; then
                if [ "$force" != "true" ]; then
                    echo "Error: Project has $APPS_COUNT applications. Use force=true to delete anyway."
                    echo "Applications in project:"
                    echo "$APPS_RESPONSE" | jq -r '.items[].metadata.name'
                    exit 1
                else
                    echo "Warning: Deleting project with $APPS_COUNT applications because force=true"
                fi
            fi
            
            echo "=== Deleting Project: $project_name ==="
            
            # Delete project
            RESPONSE=$(curl -s -k -X DELETE \
                -H "Authorization: Bearer $ARGOCD_AUTH_TOKEN" \
                "$ARGOCD_SERVER/api/v1/projects/$project_name")
            
            if [ -z "$RESPONSE" ]; then
                echo "Error: Failed to delete project"
                exit 1
            fi
            
            # Check for errors
            ERROR_CODE=$(echo "$RESPONSE" | jq -r '.code // 0')
            if [ "$ERROR_CODE" -ne 0 ]; then
                echo "Error: $(echo "$RESPONSE" | jq -r '.message')"
                exit 1
            fi
            
            echo "Project deleted successfully: $project_name"
            """,
            args=[
                Arg(name="project_name", description="Name of the ArgoCD project", required=True),
                Arg(name="force", description="Force deletion even if project has applications", required=False)
            ],
            image="curlimages/curl:8.1.2"
        ) 

ProjectTools()