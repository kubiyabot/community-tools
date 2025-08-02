from typing import List
import sys
from .base import DatadogTool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry

class MonitoringTools:
    """Datadog monitoring and analysis tools with dynamic alert handling."""

    def __init__(self):
        """Initialize and register all tools dynamically based on alert context."""
        try:
            tools = [
                self.get_alert_details(),
                self.compare_error_rates(),
                self.query_logs(),
                self.search_logs_by_string(),
                self.search_logs_by_timeframe(),
                self.get_service_map(),
                self.list_incidents(),
                self.get_incident_details()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("datadog", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Datadog monitoring tools: {str(e)}", file=sys.stderr)
            raise

    def get_alert_details(self) -> DatadogTool:
        """Retrieve details for a DataDog alert event."""
        return DatadogTool(
            name="datadog_alert_details",
            description="Retrieve details of a triggered DataDog alert (event)",
            content="""
            apk add --no-cache -q jq
            validate_datadog_connection

            if [ -z "$alert_id" ]; then
                echo "Error: Alert ID is required"
                exit 1
            fi

            ALERT_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v2/events/$alert_id" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json")

            echo "=== Alert Details ==="
            echo "$ALERT_DATA" | jq -r '
                "ID: \(.data.id)",
                "Title: \(.data.attributes.attributes.title // "N/A")",
                "Message: \(.data.attributes.message // "N/A")",
                "Service: \(.data.attributes.attributes.service // "N/A")",
                "Status: \(.data.attributes.attributes.status // "N/A")",
                "Timestamp: \(.data.attributes.attributes.timestamp // "N/A")",
                "Monitor Name: \(.data.attributes.attributes.monitor.name // "N/A")",
                "Monitor Query: \(.data.attributes.attributes.monitor.query // "N/A")",
                "Monitor Priority: \(.data.attributes.attributes.monitor.priority // "N/A")",
                "Monitor Logs URL: https://us5.datadoghq.com\(.data.attributes.attributes.monitor.result.logs_url // "N/A")",
                "Monitor Status URL: https://us5.datadoghq.com\(.data.attributes.attributes.monitor.result.alert_url // "N/A")"
            '
            """,
            args=[Arg(name="alert_id", description="ID of the alert event", required=True)],
            image="curlimages/curl:8.1.2"
        )

    def compare_error_rates(self) -> DatadogTool:
        """Compare error rates using log-based aggregation from DataDog."""
        return DatadogTool(
            name="compare_error_rates",
            description="Compare error rates for the past week vs the previous week using log aggregation",
            content="""
            apk add --no-cache -q jq coreutils
            validate_datadog_connection

            if [ -z "$service" ]; then
                echo "Error: Service name is required"
                exit 1
            fi

            echo "Comparing error rates for service: $service"

            # Calculate timestamps (in seconds)
            NOW_TS=$(date +%s)
            WEEK_SEC=604800  # 7 days in seconds
            WEEK_AGO_TS=$((NOW_TS - WEEK_SEC))
            TWO_WEEKS_AGO_TS=$((NOW_TS - (2 * WEEK_SEC)))

            fetch_current_week_logs() {
                echo "=== Fetching logs for Current Week ==="

                RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/analytics/aggregate" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "filter": {
                            "from": '"$WEEK_AGO_TS"',
                            "to": '"$NOW_TS"',
                            "query": "@service:'"$service"' @status:error"
                        },
                        "compute": [{"aggregation": "count"}],
                        "group_by": [
                            {"facet": "@service"},
                            {"facet": "@status"}
                        ]
                    }')

                if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                    echo "Error: Invalid JSON response from API"
                    echo "Raw response: $RESPONSE"
                    exit 1
                fi

                ERROR_COUNT=$(echo "$RESPONSE" | jq -r '.data.buckets[0].computes.c0 // "0"')
                echo "Total Errors in Current Week: $ERROR_COUNT"
            }

            fetch_previous_week_logs() {
                echo "=== Fetching logs for Previous Week ==="

                RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/analytics/aggregate" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "filter": {
                            "from": '"$TWO_WEEKS_AGO_TS"',
                            "to": '"$WEEK_AGO_TS"',
                            "query": "@service:'"$service"' @status:error"
                        },
                        "compute": [{"aggregation": "count"}],
                        "group_by": [
                            {"facet": "@service"},
                            {"facet": "@status"}
                        ]
                    }')

                if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                    echo "Error: Invalid JSON response from API"
                    echo "Raw response: $RESPONSE"
                    exit 1
                fi

                ERROR_COUNT=$(echo "$RESPONSE" | jq -r '.data.buckets[0].computes.c0 // "0"')
                echo "Total Errors in Previous Week: $ERROR_COUNT"
            }

            # Execute the log fetching functions
            fetch_current_week_logs
            fetch_previous_week_logs
            """,
            args=[Arg(name="service", description="Service name from alert", required=True)],
            image="curlimages/curl:8.1.2"
        )

    def query_logs(self) -> DatadogTool:
        """Dynamically query logs based on the alert's service and status."""
        return DatadogTool(
            name="query_logs",
            description="Fetch logs based on alert context",
            content="""
            apk add --no-cache -q jq
            validate_datadog_connection

            if [ -z "$service" ] || [ -z "$status" ]; then
                echo "Error: Both service and status are required"
                exit 1
            fi

            # Set default values if not provided
            LAST_HOURS="${last_hours:-1}"
            LIMIT="${limit:-10}"

            # Determine time range approach
            if [ -n "$start_time" ]; then
                # Use exact timeframe approach
                START_TIME="$start_time"
                END_TIME="${end_time:-now}"
                echo "Fetching logs for service: $service with status: $status"
                echo "Time range: $START_TIME to $END_TIME"
                echo "Limit: $LIMIT logs"
                
                TIME_FROM="$START_TIME"
                TIME_TO="$END_TIME"
            else
                # Use last hours approach
                # Validate last_hours range
                if [ "$LAST_HOURS" -lt 1 ] || [ "$LAST_HOURS" -gt 6 ]; then
                    echo "Error: last_hours must be between 1 and 6"
                    exit 1
                fi
                
                echo "Fetching logs for service: $service with status: $status"
                echo "Time range: Last $LAST_HOURS hour(s)"
                echo "Limit: $LIMIT logs"
                
                TIME_FROM="now-${LAST_HOURS}h"
                TIME_TO="now"
            fi
            
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"from\": \"$TIME_FROM\",
                        \"to\": \"$TIME_TO\",
                        \"query\": \"service:$service status:$status\"
                    },
                    \"sort\": \"timestamp\",
                    \"page\": {
                        \"limit\": $LIMIT
                    }
                }")

            # Check if response is empty
            if [ "$(echo "$RESPONSE" | jq '.data')" = "null" ]; then
                echo "No logs found for the given criteria"
                exit 0
            fi

            # Format and output the logs
            echo "$RESPONSE" | jq -r '
                "=== Found \(.meta.page.total // 0) logs ===\n" +
                (.data | map(
                    "Time: \(.attributes.timestamp)\n" +
                    "Service: \(.attributes.service)\n" +
                    "Status: \(.attributes.status)\n" +
                    "Message: \(.attributes.message)\n" +
                    "---"
                ) | join("\n"))
            '
            """,
            args=[
                Arg(name="service", description="Service name from alert", required=True),
                Arg(name="status", description="Error status from alert", required=True),
                Arg(name="last_hours", description="Number of hours to look back (1-6 hours, default: 1). Ignored if start_time is provided.", required=False),
                Arg(name="start_time", description="Exact start time (e.g. '2024-01-01T10:00:00Z', 'now-2h'). If provided, overrides last_hours.", required=False),
                Arg(name="end_time", description="Exact end time (e.g. '2024-01-01T15:00:00Z', 'now'). Only used with start_time. Default: 'now'", required=False),
                Arg(name="limit", description="Maximum number of logs to return (default: 10)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def search_logs_by_string(self) -> DatadogTool:
        """Search logs using a custom string query without time filtering."""
        return DatadogTool(
            name="search_logs_by_string",
            description="Search logs using a custom query string without time constraints, only filtered by string and limit",
            content="""
            apk add --no-cache -q jq
            validate_datadog_connection

            if [ -z "$query_string" ]; then
                echo "Error: Query string is required"
                exit 1
            fi

            # Set default limit if not provided
            LIMIT="${limit:-20}"

            echo "Searching logs with query: $query_string"
            echo "Time range: No time constraints (searching all available logs)"
            echo "Limit: $LIMIT logs"
            
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"query\": \"$query_string\"
                    },
                    \"sort\": \"timestamp\",
                    \"page\": {
                        \"limit\": $LIMIT
                    }
                }")

            # Check if response is empty
            if [ "$(echo "$RESPONSE" | jq '.data')" = "null" ]; then
                echo "No logs found matching the query: $query_string"
                exit 0
            fi

            # Format and output the logs
            echo "$RESPONSE" | jq -r '
                "=== Found \(.meta.page.total // 0) logs ===\n" +
                (.data | map(
                    "Time: \(.attributes.timestamp)\n" +
                    "Service: \(.attributes.service // "N/A")\n" +
                    "Status: \(.attributes.status // "N/A")\n" +
                    "Message: \(.attributes.message // "N/A")\n" +
                    (if .attributes.attributes then
                        "Tags: " + (.attributes.attributes | to_entries | map("\(.key):\(.value)") | join(", ")) + "\n"
                    else
                        ""
                    end) +
                    "---"
                ) | join("\n"))
            '
            """,
            args=[
                Arg(name="query_string", description="Custom query string to search logs (e.g. 'error database connection')", required=True),
                Arg(name="limit", description="Maximum number of logs to return (default: 20)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def search_logs_by_timeframe(self) -> DatadogTool:
        """Search logs within a specified timeframe."""
        return DatadogTool(
            name="search_logs_by_timeframe",
            description="Search logs within a specified timeframe with optional query filtering",
            content="""
            apk add --no-cache -q jq coreutils
            validate_datadog_connection

            if [ -z "$start_time" ] || [ -z "$end_time" ]; then
                echo "Error: Both start_time and end_time are required"
                exit 1
            fi

            # Set default values if not provided
            LIMIT="${limit:-25}"
            QUERY="${query:-}"

            echo "=== Log Search Parameters ==="
            echo "Start Time: $start_time"
            echo "End Time: $end_time"
            echo "Query: ${QUERY:-"(no filters, showing all logs)"}"
            echo "Limit: $LIMIT logs"
            
            # Execute the API call
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"from\": \"$start_time\",
                        \"to\": \"$end_time\",
                        \"query\": \"$QUERY\"
                    },
                    \"sort\": \"timestamp\",
                    \"page\": {
                        \"limit\": $LIMIT
                    }
                }")

            # Check if response is empty
            if [ "$(echo "$RESPONSE" | jq '.data')" = "null" ]; then
                echo "No logs found for the given timeframe and criteria"
                exit 0
            fi

            # Format and output the logs
            echo "$RESPONSE" | jq -r '
                "=== Found \(.meta.page.total // 0) logs ===\n" +
                (.data | map(
                    "Time: \(.attributes.timestamp)\n" +
                    "Service: \(.attributes.service // "N/A")\n" +
                    "Status: \(.attributes.status // "N/A")\n" +
                    "Message: \(.attributes.message // "N/A")\n" +
                    (if .attributes.attributes then
                        "Tags: " + (.attributes.attributes | to_entries | map("\(.key):\(.value)") | join(", ")) + "\n"
                    else
                        ""
                    end) +
                    "---"
                ) | join("\n"))
            '
            """,
            args=[
                Arg(name="start_time", description="Start time for the search (e.g. '2024-01-01T10:00:00Z', 'now-2h', timestamp)", required=True),
                Arg(name="end_time", description="End time for the search (e.g. '2024-01-01T15:00:00Z', 'now', timestamp)", required=True),
                Arg(name="query", description="Optional query string to filter logs (e.g. 'service:myapp status:error')", required=False),
                Arg(name="limit", description="Maximum number of logs to return (default: 25)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_service_map(self) -> DatadogTool:
        """Fetch and analyze the complete Service Map data from Datadog."""
        return DatadogTool(
            name="get_service_map",
            description="Retrieve complete Service Map data to visualize all service dependencies and repository mappings",
            content="""
            apk add --no-cache -q jq coreutils
            validate_datadog_connection
            
            echo "Fetching complete Service Map data"
            echo "Time range: now-1h to now"
            
            # First, query the service list to get service details
            echo "=== Querying Datadog Service List ==="
            SERVICES_RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/services" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Accept: application/json")
            
            if echo "$SERVICES_RESPONSE" | grep -q "error"; then
                echo "Error retrieving service list:"
                echo "$SERVICES_RESPONSE" | jq -r '.errors[] // .errors'
                exit 1
            fi
            
            # Create a mapping of service names to their details including repositories
            echo "=== Creating Service to Repository Mapping ==="
            echo "$SERVICES_RESPONSE" | jq -r '
                "Found \(.data | length) services in Datadog\n" +
                (.data | map(
                    "Service: \(.attributes.name)\n" +
                    "Type: \(.attributes.type // "N/A")\n" +
                    (if .attributes.tags then 
                        "Tags: " + (.attributes.tags | join(", ")) + "\n" 
                    else 
                        "Tags: N/A\n" 
                    end) +
                    (if .attributes.links then
                        "Links: " + (.attributes.links | to_entries | map("\(.key): \(.value)") | join(", ")) + "\n"
                    else
                        "Links: N/A\n"
                    end) +
                    (if .attributes.meta then
                        if .attributes.meta.repository_url then
                            "Repository: \(.attributes.meta.repository_url)\n"
                        elif .attributes.meta.repository_name then
                            "Repository: \(.attributes.meta.repository_name)\n"
                        else
                            "Repository: N/A\n"
                        end
                    else
                        "Repository: N/A\n"
                    end) +
                    "---"
                ) | join("\n"))
            '
            
            # Now fetch the service map dependencies data
            echo "=== Fetching Service Map Dependencies ==="
            DEPS_RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/service_dependencies?start=now-1h&end=now" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Accept: application/json")
            
            if echo "$DEPS_RESPONSE" | grep -q "error"; then
                echo "Error retrieving service dependencies:"
                echo "$DEPS_RESPONSE" | jq -r '.errors[] // .errors'
                exit 1
            fi
            
            # Process and output the dependencies data
            echo "=== Service Dependencies Analysis ==="
            
            # Total count of service relationships
            TOTAL_DEPS=$(echo "$DEPS_RESPONSE" | jq '.service_dependencies | length')
            echo "Total service relationships found: $TOTAL_DEPS"
            
            if [ "$TOTAL_DEPS" -gt 0 ]; then
                # Show the service dependency map
                echo "$DEPS_RESPONSE" | jq -r '
                    "Service Dependency Map:\n" +
                    (.service_dependencies | group_by(.parent) | map(
                        "Service \(.[0].parent) depends on:"
                        + 
                        (. | map("  - \(.child) (\(.type)) - \(.calls_count // 0) calls") | join("\n"))
                    ) | join("\n\n"))
                '
                
                # Create a visualization of service centrality (which services are most central/important)
                echo "=== Service Centrality Analysis ==="
                echo "$DEPS_RESPONSE" | jq -r '
                    # Count incoming dependencies (how many services depend on this service)
                    (.service_dependencies | group_by(.child) | map({
                        service: .[0].child,
                        incoming_deps: length,
                        total_calls: (. | map(.calls_count) | add)
                    }) | sort_by(-.incoming_deps) | .[0:10] | map(
                        "\(.service): \(.incoming_deps) services depend on it with \(.total_calls // 0) total calls"
                    ) | join("\n"))
                '
                
                # Extract any repository information from dependencies if available
                echo "=== Service to Repository Mapping ==="
                REPO_INFO=$(echo "$DEPS_RESPONSE" | jq -r '
                    (.service_dependencies | map({
                        service: .parent,
                        repo: (.metadata.git.repository // "N/A"),
                        repo_url: (.metadata.git.repository_url // "N/A")
                    }) | unique | map(
                        "Service: \(.service), Repository: " + 
                        if .repo != "N/A" then .repo
                        elif .repo_url != "N/A" then .repo_url
                        else "N/A"
                        end
                    ) | join("\n"))
                ')
                
                if [ "$REPO_INFO" != "" ] && [ "$REPO_INFO" != "null" ]; then
                    echo "$REPO_INFO"
                else
                    echo "No repository information found in service dependencies data."
                    echo "Repository information may be available in service definitions or APM data."
                fi
                
                # Generate summary statistics about types of dependencies
                echo "=== Dependency Type Distribution ==="
                echo "$DEPS_RESPONSE" | jq -r '
                    (.service_dependencies | group_by(.type) | map({
                        type: .[0].type,
                        count: length
                    }) | sort_by(-.count) | map(
                        "\(.type): \(.count) dependencies"
                    ) | join("\n"))
                '
            else
                echo "No service dependencies found for the specified time range."
            fi
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )

    def list_incidents(self) -> DatadogTool:
        """List all Datadog incidents with default settings."""
        return DatadogTool(
            name="list_datadog_incidents",
            description="List all Datadog incidents with default settings",
            content="""
            apk add --no-cache -q jq coreutils
            validate_datadog_connection

            echo "Fetching all incidents with default settings"
            
            # Display the full curl command (with API keys masked for security)
            echo "Executing curl command: curl -X GET \"https://api.$DD_SITE/api/v2/incidents\" -H \"DD-API-KEY: ****\" -H \"DD-APPLICATION-KEY: ****\" -H \"Content-Type: application/json\" -H \"Accept: application/json\""
            
            # Make the API call to list incidents
            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/incidents" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json")
            echo "$RESPONSE" | jq
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )

    def get_incident_details(self) -> DatadogTool:
        """Retrieve detailed information about a specific Datadog incident."""
        return DatadogTool(
            name="get_datadog_incident_details",
            description="Get detailed information about a specific incident including timeline and related data",
            content="""
            apk add --no-cache -q jq
            validate_datadog_connection

            if [ -z "$incident_id" ]; then
                echo "Error: Incident ID is required"
                exit 1
            fi

            echo "Fetching details for incident: $incident_id"
            
            # Get main incident details
            INCIDENT_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v2/incidents/$incident_id" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json")
            
            # Check for API errors
            if echo "$INCIDENT_DATA" | grep -q "error"; then
                echo "Error retrieving incident details:"
                echo "$INCIDENT_DATA" | jq -r '.errors[] // .errors'
                exit 1
            fi
            
            # Parse and display main incident information
            echo "=== Incident Overview ==="
            echo "$INCIDENT_DATA" | jq -r '
                .data | 
                "ID: \(.id)",
                "Title: \(.attributes.title)",
                "Status: \(.attributes.state)",
                "Severity: \(.attributes.severity)",
                "Created: \(.attributes.created)",
                "Modified: \(.attributes.modified)",
                "Detected: \(.attributes.detected)",
                "Created By: \(if .attributes.created_by then .attributes.created_by.handle else "Unknown" end)",
                
                "Customer Impact Summary: \(.attributes.customer_impact.summary // "None")",
                "Customer Impact Scope: \(.attributes.customer_impact.scope // "None")",
                
                if .attributes.fields then
                    "Fields: " + (.attributes.fields | map("\(.name): \(.value)") | join(", "))
                else
                    "Fields: None"
                end,
                
                "Commander: \(if .attributes.commander then .attributes.commander.handle else "None" end)",
                
                if .attributes.services then
                    "Affected Services: " + (.attributes.services | map(.name) | join(", "))
                else
                    "Affected Services: None"
                end,
                
                "Public ID: \(.attributes.public_id // "None")",
                "Visibility: \(.attributes.visibility)",
                "URL: https://app.datadoghq.com/incidents/\(.id)"
            '
            
            # Get incident timeline
            echo ""
            echo "=== Incident Timeline ==="
            
            TIMELINE_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v2/incidents/$incident_id/attachments" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json")
            
            # Parse and display timeline data
            TIMELINE_COUNT=$(echo "$TIMELINE_DATA" | jq '.data | length')
            
            if [ "$TIMELINE_COUNT" -eq 0 ]; then
                echo "No timeline entries found for this incident."
            else
                echo "$TIMELINE_DATA" | jq -r '
                    .data | sort_by(.attributes.created) | map(
                        "Time: \(.attributes.created)",
                        "Type: \(.attributes.attachment_type)",
                        if .attributes.attachment_type == "timeline_cell" then
                            "Content: \(.attributes.attributes.cell_content // "No content")"
                        elif .attributes.attachment_type == "postmortem" then
                            "Postmortem: \(.attributes.attributes.document_url // "No URL")"
                        elif .attributes.attachment_type == "link" then
                            "Link: \(.attributes.attributes.url // "No URL")\nTitle: \(.attributes.attributes.title // "No title")"
                        else
                            "Content: \(.attributes // "No details")"
                        end,
                        "---"
                    ) | join("\n")
                '
            fi
            
            # Get incident updates
            echo ""
            echo "=== Incident Updates ==="
            
            UPDATES_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v2/incidents/$incident_id/relationships/updates" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json")
            
            UPDATES_COUNT=$(echo "$UPDATES_DATA" | jq '.data | length')
            
            if [ "$UPDATES_COUNT" -eq 0 ]; then
                echo "No updates recorded for this incident."
            else
                echo "$UPDATES_DATA" | jq -r '
                    .data | sort_by(.attributes.created) | map(
                        "Time: \(.attributes.created)",
                        "Updated by: \(if .attributes.created_by then .attributes.created_by.handle else "Unknown" end)",
                        "Content: \(.attributes.content // "No content")",
                        "---"
                    ) | join("\n")
                '
            fi
            """,
            args=[
                Arg(name="incident_id", description="ID of the incident to retrieve", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize tools
MonitoringTools()
