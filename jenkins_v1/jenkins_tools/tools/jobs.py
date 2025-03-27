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
                self.get_job_logs(),
                self.get_queue_item()
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
                echo "Installing jq..."
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            echo "Validating Jenkins connection..."
            validate_jenkins_connection

            if [ -z "$job_name" ]; then
                echo "Error: Job name is required"
                exit 1
            fi

            # Construct parameters string if provided
            PARAMS=""
            if [ ! -z "$parameters" ]; then
                echo "Parameters provided, constructing parameters string..."
                PARAMS="--data-urlencode json='{\"parameter\": $parameters}'"
                echo "Parameters string: $PARAMS"
            fi

            # Prepare trigger URL
            TRIGGER_URL="$JENKINS_URL/job/$job_name/build"
            if [ ! -z "$parameters" ]; then
                TRIGGER_URL="$JENKINS_URL/job/$job_name/buildWithParameters"
            fi
            echo "Using trigger URL: $TRIGGER_URL"

            # Trigger the build and store full response
            echo "Sending POST request to Jenkins..."
            RESPONSE=$(curl -sS -i -w "\\nHTTP_STATUS:%{http_code}" -X POST -u "$JENKINS_USER:$JENKINS_TOKEN" $PARAMS "$TRIGGER_URL")
            echo "Received response from Jenkins"
            
            HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d':' -f2)
            echo "HTTP Status Code: $HTTP_STATUS"
            
            QUEUE_URL=$(echo "$RESPONSE" | grep -i "^location: " | cut -d' ' -f2 | tr -d '\\r')
            echo "Queue URL from response: $QUEUE_URL"
            
            RESPONSE_BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:" | grep -v "^HTTP/")
            echo "Response headers:"
            echo "$RESPONSE" | grep "^HTTP\|^Location\|^Date"

            # Check HTTP status code
            if [ "$HTTP_STATUS" -eq 201 ] || [ "$HTTP_STATUS" -eq 200 ]; then
                echo "Build request successful, extracting queue ID..."
                
                # Extract queue ID from the location URL using a simpler method
                QUEUE_ID=$(echo "$QUEUE_URL" | grep -o '/[0-9]*/' | tr -d '/')
                echo "Extracted queue ID: '$QUEUE_ID'"
                
                if [ -z "$QUEUE_ID" ]; then
                    echo "Error: Could not extract queue ID from response"
                    echo "Location URL: $QUEUE_URL"
                    echo "Full response for debugging:"
                    echo "$RESPONSE"
                    exit 1
                fi
                
                echo "Build triggered successfully"
                echo "Queue ID: $QUEUE_ID"
                echo "Queue URL: $QUEUE_URL"
                echo "Checking for build number (30 second timeout)..."
                
                # Try to get build number for 30 seconds using queue item
                COUNTER=1
                while [ $COUNTER -le 30 ]; do
                    echo "Attempt $COUNTER/30: Checking build status..."
                    
                    # Get queue item info
                    QUEUE_INFO_URL="$JENKINS_URL/queue/item/$QUEUE_ID/api/json"
                    echo "Fetching queue info from: $QUEUE_INFO_URL"
                    
                    QUEUE_INFO=$(curl -sS -u "$JENKINS_USER:$JENKINS_TOKEN" "$QUEUE_INFO_URL")
                    echo "Queue info response: $QUEUE_INFO"
                    
                    # Check if the build has started
                    BUILD_NUMBER=$(echo "$QUEUE_INFO" | jq -r '.executable.number // empty')
                    echo "Build number from queue info: '$BUILD_NUMBER'"
                    
                    if [ ! -z "$BUILD_NUMBER" ]; then
                        echo "Build started:"
                        echo "build_number: $BUILD_NUMBER"
                        echo "build_url: $JENKINS_URL/job/$job_name/$BUILD_NUMBER"
                        exit 0
                    fi
                    
                    echo "Build not started yet, waiting 1 second..."
                    sleep 1
                    COUNTER=$((COUNTER + 1))
                done
                
                # If we get here, build hasn't started within timeout
                echo "Build still in queue after 30 seconds:"
                echo "queue_id: $QUEUE_ID"
                echo "queue_url: $QUEUE_URL"
                echo ""
                echo "To get the build number once it starts, run:"
                echo "get_queue_item queue_id=$QUEUE_ID"
            else
                echo "Error: Failed to trigger build"
                echo "Status code: $HTTP_STATUS"
                echo "Response body: $RESPONSE_BODY"
                echo "Full response for debugging:"
                echo "$RESPONSE"
                exit 1
            fi
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job to trigger",
                    required=True),
                Arg(name="parameters",
                    description="JSON string of build parameters",
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

    def get_queue_item(self) -> JenkinsTool:
        """Get build information from a queue item ID."""
        return JenkinsTool(
            name="get_queue_item",
            description="Get build information for a specific queue item",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            if [ -z "$queue_id" ]; then
                echo "Error: Queue ID is required"
                exit 1
            fi

            # Get queue item information
            QUEUE_URL="$JENKINS_URL/queue/item/$queue_id/api/json"
            QUEUE_INFO=$(curl -sS -u "$JENKINS_USER:$JENKINS_TOKEN" "$QUEUE_URL")
            
            # Check if request was successful
            if [ $? -ne 0 ]; then
                echo "Error: Failed to get queue item information"
                exit 1
            fi

            # Extract relevant information
            TASK_NAME=$(echo "$QUEUE_INFO" | jq -r '.task.name')
            WHY=$(echo "$QUEUE_INFO" | jq -r '.why // "N/A"')
            STUCK=$(echo "$QUEUE_INFO" | jq -r '.stuck')
            BUILDABLE=$(echo "$QUEUE_INFO" | jq -r '.buildable')
            BUILD_NUMBER=$(echo "$QUEUE_INFO" | jq -r '.executable.number // empty')
            
            echo "=== Queue Item Information ==="
            echo "Queue ID: $queue_id"
            echo "Job Name: $TASK_NAME"
            
            if [ ! -z "$BUILD_NUMBER" ]; then
                echo "Status: BUILDING"
                echo "Build Number: #$BUILD_NUMBER"
                echo "Build URL: $JENKINS_URL/job/$TASK_NAME/$BUILD_NUMBER"
                
                # Get build status if build has started
                BUILD_INFO=$(curl -sS -u "$JENKINS_USER:$JENKINS_TOKEN" "$JENKINS_URL/job/$TASK_NAME/$BUILD_NUMBER/api/json")
                BUILD_RESULT=$(echo "$BUILD_INFO" | jq -r '.result // "IN PROGRESS"')
                BUILDING=$(echo "$BUILD_INFO" | jq -r '.building')
                
                echo "Build Status: $BUILD_RESULT"
                echo "Still Building: $BUILDING"
            else
                echo "Status: QUEUED"
                echo "Why Waiting: $WHY"
                echo "Stuck: $STUCK"
                echo "Buildable: $BUILDABLE"
            fi
            """,
            args=[
                Arg(name="queue_id",
                    description="Jenkins queue item ID to look up",
                    required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize when module is imported
JobManager() 