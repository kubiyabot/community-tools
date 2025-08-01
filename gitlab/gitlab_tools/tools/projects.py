from typing import List
from .base import GitLabTool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry
import sys

class ProjectManager:
    """Manage GitLab projects."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Register all tools
            tools = [
                self.create_project(),
                self.list_projects(),
                self.get_project_details(),
                self.list_project_branches(),
                self.list_project_commits(),
                self.list_pipelines(),
                self.trigger_pipeline(),
                self.get_pipeline_status(),
                self.get_pipeline_jobs(),
                self.retry_pipeline(),
                self.cancel_pipeline()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("gitlab", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register GitLab tools: {str(e)}", file=sys.stderr)
            raise

    def create_project(self) -> GitLabTool:
        """Create a new GitLab project."""
        return GitLabTool(
            name="create_project",
            description="Create a new GitLab project",
            content="""
            if [ -z "$project_name" ]; then
                echo "Error: Project name not specified"
                exit 1
            fi

            # Create project using GitLab API
            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                 --header "Content-Type: application/json" \
                 --data "{
                   \\"name\\": \\"$project_name\\",
                   \\"description\\": \\"$description\\",
                   \\"visibility\\": \\"$visibility\\"
                 }" \
                 --request POST \
                 "$GITLAB_API_URL/projects"
            """,
            args=[
                Arg(name="project_name",
                    description="Name of the project to create",
                    required=True),
                Arg(name="description",
                    description="Project description",
                    required=False),
                Arg(name="visibility",
                    description="Project visibility (private/internal/public)",
                    required=False)
            ],
            image="alpine/curl:latest"
        )

    def list_projects(self) -> GitLabTool:
        """List GitLab projects."""
        return GitLabTool(
            name="list_projects",
            description="List GitLab projects",
            content="""
            # List projects using GitLab API
            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                 "$GITLAB_API_URL/projects?membership=true&per_page=100"
            """,
            args=[],
            image="alpine/curl:latest"
        )

    def get_project_details(self) -> GitLabTool:
        """Get details about a specific project."""
        return GitLabTool(
            name="get_project_details",
            description="Get detailed information about a specific project",
            content="""
            if [ -z "$project_id" ]; then
                echo "Error: Project ID not specified"
                exit 1
            fi

            # Get project details using GitLab API
            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                 "$GITLAB_API_URL/projects/$project_id"
            """,
            args=[
                Arg(name="project_id",
                    description="ID of the project",
                    required=True)
            ],
            image="alpine/curl:latest"
        )

    def list_project_branches(self) -> GitLabTool:
        """List branches in a project."""
        return GitLabTool(
            name="list_project_branches",
            description="List all branches in a specific project",
            content="""
            if [ -z "$project_id" ]; then
                echo "Error: Project ID not specified"
                exit 1
            fi

            # List branches using GitLab API
            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                 "$GITLAB_API_URL/projects/$project_id/repository/branches"
            """,
            args=[
                Arg(name="project_id",
                    description="ID or URL-encoded path of the project",
                    required=True)
            ],
            image="alpine/curl:latest"
        )

    def list_project_commits(self) -> GitLabTool:
        """List recent commits in a project."""
        return GitLabTool(
            name="list_project_commits",
            description="List recent commits in a specific project",
            content="""
            if [ -z "$project_id" ]; then
                echo "Error: Project ID not specified"
                exit 1
            fi

            # List commits using GitLab API
            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                 "$GITLAB_API_URL/projects/$project_id/repository/commits?per_page=10"
            """,
            args=[
                Arg(name="project_id",
                    description="ID or URL-encoded path of the project",
                    required=True)
            ],
            image="alpine/curl:latest"
        )
    
    def trigger_pipeline(self) -> GitLabTool:
        """Trigger a GitLab CI/CD pipeline manually."""
        return GitLabTool(
            name="trigger_pipeline",
            description="Trigger a pipeline for a specific GitLab project and branch",
            content="""
            if [ -z "$project_id" ] || [ -z "$branch" ]; then
                echo "Error: Project ID and branch are required"
                exit 1
            fi

            curl --request POST \
                --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                --header "Content-Type: application/json" \
                --data "{
                    \\"ref\\": \\"$branch\\"
                }" \
                "$GITLAB_API_URL/projects/$project_id/pipeline"
            """,
            args=[
                Arg(name="project_id", description="ID of the project", required=True),
                Arg(name="branch", description="Branch to trigger the pipeline", required=True)
            ],
            image="alpine/curl:latest"
        )
   
    def get_pipeline_status(self) -> GitLabTool:
        """Get the latest pipeline status for a project."""
        return GitLabTool(
            name="get_pipeline_status",
            description="Fetch the latest pipeline status for a project",
            content="""
            if [ -z "$project_id" ]; then
                echo "Error: Project ID is required"
                exit 1
            fi

            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                "$GITLAB_API_URL/projects/$project_id/pipelines?per_page=1"
            """,
            args=[
                Arg(name="project_id", description="ID of the project", required=True)
            ],
            image="alpine/curl:latest"
        )

    def get_pipeline_jobs(self) -> GitLabTool:
        """Get jobs for a specific pipeline."""
        return GitLabTool(
            name="get_pipeline_jobs",
            description="Get all jobs in a pipeline",
            content="""
            if [ -z "$project_id" ] || [ -z "$pipeline_id" ]; then
                echo "Error: Project ID and pipeline ID are required"
                exit 1
            fi

            curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                "$GITLAB_API_URL/projects/$project_id/pipelines/$pipeline_id/jobs"
            """,
            args=[
                Arg(name="project_id", description="ID of the project", required=True),
                Arg(name="pipeline_id", description="ID of the pipeline", required=True)
            ],
            image="alpine/curl:latest"
        )

    def retry_pipeline(self) -> GitLabTool:
        """Retry a failed pipeline."""
        return GitLabTool(
            name="retry_pipeline",
            description="Retry a failed pipeline",
            content="""
            if [ -z "$project_id" ] || [ -z "$pipeline_id" ]; then
                echo "Error: Project ID and pipeline ID are required"
                exit 1
            fi

            curl --request POST \
                --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                "$GITLAB_API_URL/projects/$project_id/pipelines/$pipeline_id/retry"
            """,
            args=[
                Arg(name="project_id", description="ID of the project", required=True),
                Arg(name="pipeline_id", description="ID of the pipeline to retry", required=True)
            ],
            image="alpine/curl:latest"
        )

    def cancel_pipeline(self) -> GitLabTool:
        """Cancel a running pipeline."""
        return GitLabTool(
            name="cancel_pipeline",
            description="Cancel a running pipeline",
            content="""
            if [ -z "$project_id" ] || [ -z "$pipeline_id" ]; then
                echo "Error: Project ID and pipeline ID are required"
                exit 1
            fi

            curl --request POST \
                --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                "$GITLAB_API_URL/projects/$project_id/pipelines/$pipeline_id/cancel"
            """,
            args=[
                Arg(name="project_id", description="ID of the project", required=True),
                Arg(name="pipeline_id", description="ID of the pipeline to cancel", required=True)
            ],
            image="alpine/curl:latest"
        )

    def list_pipelines(self) -> GitLabTool:
        """List pipelines for a project."""
        return GitLabTool(
            name="list_pipelines",
            description="List pipelines for a specific project",
            content="""
            if [ -z "$project_id" ]; then
                echo "Error: Project ID not specified"
                exit 1
            fi

            # Optional status filter
            STATUS_FILTER=""
            if [ ! -z "$status" ]; then
                STATUS_FILTER="&status=$status"
            fi

            # Set page size
            PER_PAGE=100
            if [ "$all" = "true" ]; then
                # First, get total number of pipelines
                TOTAL=$(curl --silent --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                    "$GITLAB_API_URL/projects/$project_id/pipelines?per_page=1" | \
                    grep -i "x-total:" | cut -d' ' -f2 | tr -d '\\r')
                
                # Calculate number of pages needed
                PAGES=$(( ($TOTAL + $PER_PAGE - 1) / $PER_PAGE ))
                
                echo "{ \\"pipelines\\": ["
                
                for PAGE in $(seq 1 $PAGES); do
                    RESPONSE=$(curl --silent --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                        "$GITLAB_API_URL/projects/$project_id/pipelines?per_page=$PER_PAGE&page=$PAGE$STATUS_FILTER")
                    
                    # Remove the opening and closing brackets
                    RESPONSE=${RESPONSE#[}
                    RESPONSE=${RESPONSE%]}
                    
                    # Add comma if not last page
                    if [ $PAGE -lt $PAGES ]; then
                        echo "$RESPONSE,"
                    else
                        echo "$RESPONSE"
                    fi
                done
                
                echo "]}"
            else
                # Default behavior - return first 20 pipelines
                curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                    "$GITLAB_API_URL/projects/$project_id/pipelines?per_page=20$STATUS_FILTER"
            fi
            """,
            args=[
                Arg(name="project_id", 
                    description="ID of the project", 
                    required=True),
                Arg(name="status",
                    description="Filter by status (running, pending, success, failed, canceled)",
                    required=False),
                Arg(name="all",
                    description="Set to 'true' to fetch all pipelines (default: false)",
                    required=False)
            ],
            image="alpine/curl:latest"
        )


# Initialize when module is imported
ProjectManager() 