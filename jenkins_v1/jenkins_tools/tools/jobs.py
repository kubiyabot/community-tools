from typing import List
import sys
from .base import JenkinsTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class JobManager:
    """Manage Jenkins jobs and their execution."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            tools = [
                self.trigger_job(),
                self.get_build_status(),
                self.list_jobs(),
                self.get_job_logs()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("jenkins", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register Jenkins job tools: {str(e)}", file=sys.stderr)
            raise

    def trigger_job(self) -> JenkinsTool:
        """Trigger a Jenkins job with optional parameters."""
        return JenkinsTool(
            name="trigger_job",
            description="Trigger a Jenkins job with optional parameters",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            if [ -z "$job_name" ]; then
                echo "Error: Job name is required"
                exit 1
            fi

            # Construct parameters string if provided
            PARAMS=""
            if [ ! -z "$parameters" ]; then
                PARAMS="--data-urlencode json='{\"parameter\": $parameters}'"
            fi

            # Trigger the build
            echo "Triggering job: $job_name"
            TRIGGER_URL="$JENKINS_URL/job/$job_name/build"
            
            if [ ! -z "$parameters" ]; then
                TRIGGER_URL="$JENKINS_URL/job/$job_name/buildWithParameters"
            fi

            # Use eval to properly handle the parameters string
            RESPONSE=$(eval "curl -sS -X POST -u \"$JENKINS_USER:$JENKINS_TOKEN\" $PARAMS $TRIGGER_URL")
            
            # Get queue item location
            QUEUE_URL=$(curl -sS -I -u "$JENKINS_USER:$JENKINS_TOKEN" "$TRIGGER_URL" | grep "Location:" | cut -d' ' -f2 | tr -d '\\r')
            
            if [ ! -z "$QUEUE_URL" ]; then
                echo "Build triggered successfully"
                echo "Queue URL: $QUEUE_URL"
                
                if [ "$wait_for_start" = "true" ]; then
                    echo "Waiting for build to start..."
                    # Poll queue item until it converts to a build
                    for i in {1..30}; do
                        sleep 2
                        BUILD_NUMBER=$(curl -sS -u "$JENKINS_USER:$JENKINS_TOKEN" "$QUEUE_URL"api/json | jq -r '.executable.number // empty')
                        if [ ! -z "$BUILD_NUMBER" ]; then
                            echo "Build started - Build #$BUILD_NUMBER"
                            echo "Build URL: $JENKINS_URL/job/$job_name/$BUILD_NUMBER"
                            break
                        fi
                    done
                fi
            else
                echo "Failed to trigger build"
                exit 1
            fi
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job to trigger",
                    required=True),
                Arg(name="parameters",
                    description="JSON string of build parameters",
                    required=False),
                Arg(name="wait_for_start",
                    description="Wait for the build to start and get build number",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_build_status(self) -> JenkinsTool:
        """Get the status of a specific build."""
        return JenkinsTool(
            name="get_build_status",
            description="Get the status and details of a specific build",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            if [ -z "$job_name" ]; then
                echo "Error: Job name is required"
                exit 1
            fi

            BUILD_NUM=${build_number:-"lastBuild"}
            BUILD_URL="$JENKINS_URL/job/$job_name/$BUILD_NUM/api/json"

            echo "Fetching build status for $job_name #$BUILD_NUM..."
            
            # Get build information
            BUILD_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL")
            
            echo "=== Build Status ==="
            echo "Job: $job_name"
            echo "Build: #$(echo "$BUILD_INFO" | jq -r '.number')"
            echo "Result: $(echo "$BUILD_INFO" | jq -r '.result // "IN PROGRESS"')"
            echo "Status: $(echo "$BUILD_INFO" | jq -r '.building' | sed 's/true/BUILDING/;s/false/COMPLETED/')"
            echo "Duration: $(echo "$BUILD_INFO" | jq -r '.duration') ms"
            echo "URL: $(echo "$BUILD_INFO" | jq -r '.url')"
            
            if [ "$include_changes" = "true" ]; then
                echo "\n=== Changes ==="
                echo "$BUILD_INFO" | jq -r '.changeSet.items[] | "- " + .msg' || echo "No changes found"
            fi
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number",
                    description="Build number (defaults to lastBuild)",
                    required=False),
                Arg(name="include_changes",
                    description="Include change information",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def list_jobs(self) -> JenkinsTool:
        """List all Jenkins jobs with optional filtering."""
        return JenkinsTool(
            name="list_jobs",
            description="List all Jenkins jobs with optional filtering",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            echo "Fetching Jenkins jobs..."

            # Get all jobs
            JOBS=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$JENKINS_URL/api/json")

            # Apply folder filter if specified
            if [ ! -z "$folder" ]; then
                JOBS=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$JENKINS_URL/job/$folder/api/json")
            fi

            echo "=== Jenkins Jobs ==="

            # Process and filter jobs
            echo "$JOBS" | jq -r --arg status "$status" --arg name_filter "$name_filter" '
                .jobs[] | 
                select(
                    ($status == "" or 
                    ($status == "active" and .color != "disabled") or 
                    ($status == "disabled" and .color == "disabled")) and
                    ($name_filter == "" or (.name | contains($name_filter)))
                ) | 
                "Name: " + .name + 
                "\nURL: " + .url +
                "\nStatus: " + (if .color == "disabled" then "Disabled" else "Active" end) +
                if .lastBuild then "\nLast Build: #" + (.lastBuild.number | tostring) else "\nNo builds" end +
                "\n"
            '
            """,
            args=[
                Arg(name="folder",
                    description="Jenkins folder to list jobs from",
                    required=False),
                Arg(name="status",
                    description="Filter by job status (active/disabled)",
                    required=False),
                Arg(name="name_filter",
                    description="Filter jobs by name",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_job_logs(self) -> JenkinsTool:
        """Get logs from a specific job build."""
        return JenkinsTool(
            name="get_job_logs",
            description="Get console logs from a specific job build",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            if [ -z "$job_name" ]; then
                echo "Error: Job name is required"
                exit 1
            fi

            BUILD_NUM=${build_number:-"lastBuild"}
            BUILD_URL="$JENKINS_URL/job/$job_name/$BUILD_NUM"

            echo "=== Build Information ==="
            echo "Job: $job_name"
            echo "Build: #$BUILD_NUM"
            echo "URL: $BUILD_URL"

            # Get build status
            STATUS=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/api/json" | jq -r '.result // "IN PROGRESS"')
            echo "Status: $STATUS"

            echo "\n=== Console Log ==="
            if [ "$tail_lines" ]; then
                # Get only the specified number of lines from the end
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText" | tail -n "$tail_lines"
            else
                # Get full log
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText"
            fi

            if [ "$highlight_errors" = "true" ]; then
                echo "\n=== Error Highlights ==="
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText" | \
                    grep -i --color=always "error\\|exception\\|failed\\|failure" || echo "No errors found"
            fi
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number",
                    description="Build number (defaults to lastBuild)",
                    required=False),
                Arg(name="tail_lines",
                    description="Number of lines to show from the end of the log",
                    required=False),
                Arg(name="highlight_errors",
                    description="Highlight error messages in the log",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize when module is imported
JobManager() 