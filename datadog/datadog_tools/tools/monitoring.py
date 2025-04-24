from typing import List
import sys
from .base import DatadogTool, Arg
from kubiya_sdk.tools.registry import tool_registry

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
                self.get_service_map()
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
            apk add --no-cache jq
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
            apk add --no-cache jq coreutils
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
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$service" ] || [ -z "$status" ]; then
                echo "Error: Both service and status are required"
                exit 1
            fi

            echo "Fetching logs for service: $service with status: $status"
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"from\": \"now-1h\",
                        \"to\": \"now\",
                        \"query\": \"service:$service status:$status\"
                    },
                    \"sort\": \"timestamp\",
                    \"page\": {
                        \"limit\": 10
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
                Arg(name="status", description="Error status from alert", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )
        
    def search_logs_by_string(self) -> DatadogTool:
        """Search logs using a custom string query."""
        return DatadogTool(
            name="search_logs_by_string",
            description="Search logs using a custom query string with flexible time range",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$query_string" ]; then
                echo "Error: Query string is required"
                exit 1
            fi

            # Set default time range if not provided
            TIME_FROM="${time_from:-now-1h}"
            TIME_TO="${time_to:-now}"
            LIMIT="${limit:-20}"

            echo "Searching logs with query: $query_string"
            echo "Time range: $TIME_FROM to $TIME_TO"
            echo "Limit: $LIMIT logs"
            
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"from\": \"$TIME_FROM\",
                        \"to\": \"$TIME_TO\",
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
                Arg(name="time_from", description="Start time for log search (e.g. 'now-24h', 'now-7d')", required=False),
                Arg(name="time_to", description="End time for log search (default: 'now')", required=False),
                Arg(name="limit", description="Maximum number of logs to return (default: 20)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def search_logs_by_timeframe(self) -> DatadogTool:
        """Search logs within a specific time range with detailed time parsing."""
        return DatadogTool(
            name="search_logs_by_timeframe",
            description="Search logs within specific time periods with precise time control",
            content="""
            apk add --no-cache jq coreutils
            validate_datadog_connection

            # Parse time inputs (support both relative and absolute time formats)
            # Default to the last hour if not specified
            TIME_PERIOD="${time_period:-hour}"
            DURATION="${duration:-1}"
            
            # Calculate timestamps based on input time period
            NOW_TS=$(date +%s)
            
            case "$TIME_PERIOD" in
                minute)
                    TIME_UNIT=60
                    ;;
                hour)
                    TIME_UNIT=3600
                    ;;
                day)
                    TIME_UNIT=86400
                    ;;
                week)
                    TIME_UNIT=604800
                    ;;
                month)
                    TIME_UNIT=2592000  # 30 days approximation
                    ;;
                *)
                    echo "Error: Invalid time period. Use minute, hour, day, week, or month."
                    exit 1
                    ;;
            esac
            
            # Calculate from time based on duration
            FROM_TS=$((NOW_TS - (TIME_UNIT * DURATION)))
            
            # Override with absolute timestamps if provided
            if [ -n "$from_timestamp" ]; then
                FROM_TS=$from_timestamp
            fi
            
            TO_TS=$NOW_TS
            if [ -n "$to_timestamp" ]; then
                TO_TS=$to_timestamp
            fi
            
            # Set default service if provided
            SERVICE_FILTER=""
            if [ -n "$service" ]; then
                SERVICE_FILTER="service:$service"
            fi
            
            # Combine status filter if provided
            STATUS_FILTER=""
            if [ -n "$status" ]; then
                if [ -n "$SERVICE_FILTER" ]; then
                    STATUS_FILTER=" AND status:$status"
                else
                    STATUS_FILTER="status:$status"
                fi
            fi
            
            # Combine additional filter string if provided
            ADDITIONAL_FILTER=""
            if [ -n "$additional_filter" ]; then
                if [ -n "$SERVICE_FILTER" ] || [ -n "$STATUS_FILTER" ]; then
                    ADDITIONAL_FILTER=" AND $additional_filter"
                else
                    ADDITIONAL_FILTER="$additional_filter"
                fi
            fi
            
            # Combine all filters
            QUERY="${SERVICE_FILTER}${STATUS_FILTER}${ADDITIONAL_FILTER}"
            
            # Default limit
            LIMIT="${limit:-25}"
            
            echo "=== Log Search Parameters ==="
            echo "Time Range: $(date -d @$FROM_TS) to $(date -d @$TO_TS)"
            if [ -n "$QUERY" ]; then
                echo "Query: $QUERY"
            else
                echo "Query: (no filters, showing all logs)"
            fi
            echo "Limit: $LIMIT logs"
            
            # Execute the API call
            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                --data-binary "{
                    \"filter\": {
                        \"from\": $FROM_TS,
                        \"to\": $TO_TS,
                        \"query\": \"$QUERY\"
                    },
                    \"sort\": \"timestamp\",
                    \"page\": {
                        \"limit\": $LIMIT
                    }
                }")
            
            # Check for API errors
            if echo "$RESPONSE" | grep -q "error"; then
                echo "Error in API response:"
                echo "$RESPONSE" | jq -r '.errors[] // .errors'
                exit 1
            fi
            
            # Check if response is empty
            if [ "$(echo "$RESPONSE" | jq '.data')" = "null" ] || [ "$(echo "$RESPONSE" | jq '.data | length')" = "0" ]; then
                echo "No logs found for the specified time range and filters"
                exit 0
            fi
            
            # Format and output the logs with detailed attributes
            echo "$RESPONSE" | jq -r '
                "=== Found \(.meta.page.total // 0) logs for the specified time range ===\n" +
                (.data | map(
                    "Timestamp: \(.attributes.timestamp)\n" +
                    "Service: \(.attributes.service // "N/A")\n" +
                    "Status: \(.attributes.status // "N/A")\n" +
                    "Host: \(.attributes.host // "N/A")\n" +
                    "Message: \(.attributes.message // "N/A")\n" +
                    (if .attributes.attributes then
                        "Tags: " + (.attributes.attributes | to_entries | map("\(.key):\(.value)") | join(", ")) + "\n"
                    else
                        ""
                    end) +
                    "---"
                ) | join("\n"))
            '
            
            # Offer summary statistics if more than 5 logs returned
            LOG_COUNT=$(echo "$RESPONSE" | jq '.meta.page.total')
            if [ "$LOG_COUNT" -gt 5 ]; then
                echo ""
                echo "=== Log Summary Statistics ==="
                
                # Count by service
                echo "$RESPONSE" | jq -r '
                    "Services breakdown: " + 
                    (.data | group_by(.attributes.service) | map({service: .[0].attributes.service, count: length}) | 
                     map("\(.service // "unknown"): \(.count)") | join(", "))
                '
                
                # Count by status
                echo "$RESPONSE" | jq -r '
                    "Status breakdown: " + 
                    (.data | group_by(.attributes.status) | map({status: .[0].attributes.status, count: length}) | 
                     map("\(.status // "unknown"): \(.count)") | join(", "))
                '
            fi
            """,
            args=[
                Arg(name="time_period", description="Time unit to search (minute, hour, day, week, month)", required=False),
                Arg(name="duration", description="Number of time units to look back", required=False),
                Arg(name="from_timestamp", description="Specific start timestamp in Unix epoch format", required=False),
                Arg(name="to_timestamp", description="Specific end timestamp in Unix epoch format", required=False),
                Arg(name="service", description="Filter logs by service name", required=False),
                Arg(name="status", description="Filter logs by status (error, warning, info, etc.)", required=False),
                Arg(name="additional_filter", description="Additional filter criteria in Datadog query syntax", required=False),
                Arg(name="limit", description="Maximum number of logs to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_service_map(self) -> DatadogTool:
        """Fetch and analyze the Service Map data from Datadog."""
        return DatadogTool(
            name="get_service_map",
            description="Retrieve Service Map data to visualize service dependencies and repository mappings",
            content="""
            apk add --no-cache jq coreutils
            validate_datadog_connection
            
            # Default to last hour if not specified
            TIME_FROM="${time_from:-now-1h}"
            TIME_TO="${time_to:-now}"
            
            # Focus on a specific service or get all services
            SERVICE_FILTER=""
            if [ -n "$service" ]; then
                echo "Fetching Service Map data focused on service: $service"
                SERVICE_FILTER="&service=$service"
            else
                echo "Fetching complete Service Map data"
            fi
            
            echo "Time range: $TIME_FROM to $TIME_TO"
            
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
            DEPS_RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/service_dependencies?start=$TIME_FROM&end=$TIME_TO$SERVICE_FILTER" \
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
                if [ -n "$service" ]; then
                    echo "Try extending the time range or checking if the service name is correct."
                fi
            fi
            
            # If a specific service was requested, show more detailed information about it
            if [ -n "$service" ]; then
                echo "=== Detailed Analysis for Service: $service ==="
                
                # Find all upstream dependencies (services that call this service)
                echo "Upstream Dependencies (services that call $service):"
                UPSTREAM=$(echo "$DEPS_RESPONSE" | jq -r --arg svc "$service" '
                    (.service_dependencies | map(select(.child == $svc)) | map({
                        caller: .parent,
                        type: .type,
                        calls: .calls_count,
                        latency: .latency
                    }) | sort_by(-.calls) | map(
                        "\(.caller) (\(.type)) - \(.calls // 0) calls, avg latency: \(.latency // "N/A")ms"
                    ) | join("\n"))
                ')
                
                if [ "$UPSTREAM" != "" ] && [ "$UPSTREAM" != "null" ]; then
                    echo "$UPSTREAM"
                else
                    echo "No upstream dependencies found."
                fi
                
                # Find all downstream dependencies (services called by this service)
                echo "Downstream Dependencies (services called by $service):"
                DOWNSTREAM=$(echo "$DEPS_RESPONSE" | jq -r --arg svc "$service" '
                    (.service_dependencies | map(select(.parent == $svc)) | map({
                        called: .child,
                        type: .type,
                        calls: .calls_count,
                        latency: .latency
                    }) | sort_by(-.calls) | map(
                        "\(.called) (\(.type)) - \(.calls // 0) calls, avg latency: \(.latency // "N/A")ms"
                    ) | join("\n"))
                ')
                
                if [ "$DOWNSTREAM" != "" ] && [ "$DOWNSTREAM" != "null" ]; then
                    echo "$DOWNSTREAM"
                else
                    echo "No downstream dependencies found."
                fi
            fi
            """,
            args=[
                Arg(name="service", description="Specific service to focus on in the Service Map", required=False),
                Arg(name="time_from", description="Start time for Service Map data (e.g., 'now-24h')", required=False),
                Arg(name="time_to", description="End time for Service Map data (default: 'now')", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize tools
MonitoringTools()
