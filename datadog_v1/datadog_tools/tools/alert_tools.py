from typing import List
import sys
from .base import DatadogTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class AlertTools:
    """Tools for managing Datadog alerts."""

    def __init__(self):
        """Initialize and register alert management tools."""
        try:
            tools = [
                self.list_active_alerts(),
                self.get_alert_details(),
                self.get_alert_history(),
                self.compare_error_rates(),
                self.query_alert_logs(),
                self.compare_error_rates(),
                self.get_alert_by_name()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("datadog", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Datadog alert tools: {str(e)}", file=sys.stderr)
            raise

    def list_active_alerts(self) -> DatadogTool:
        """List all currently triggered alerts."""
        return DatadogTool(
            name="list_active_alerts",
            description="List all currently active/triggered alerts",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            NOW=$(date +%s)
            HOUR_AGO=$((NOW - 3600))

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -G -d "group_states=alert")

            echo "=== Currently Active Alerts ==="
            echo "$RESPONSE" | jq -r '.[] | select(.overall_state=="Alert") | 
                "Monitor ID: \(.id)\n" +
                "Name: \(.name)\n" +
                "Status: \(.overall_state)\n" +
                "Last Triggered: \(.last_triggered_ts // "Unknown")\n" +
                "Priority: \(.priority // "None")\n" +
                "---"'
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )

    def get_alert_details(self) -> DatadogTool:
        """Retrieve details for a specific alert event."""
        return DatadogTool(
            name="get_alert_details",
            description="Retrieve details of a specific alert by ID",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$alert_id" ]; then
                echo "Error: Alert ID is required"
                exit 1
            fi

            # Get current timestamp and 1 hour ago in milliseconds
            NOW_MS=$(date +%s)000
            HOUR_AGO_MS=$(( $(date +%s) - 3600 ))000
            
            # Debug time info
            echo "🕒 Current time: $(date)"
            echo "🕐 Hour ago: $(date -d "@$(( $(date +%s) - 3600 ))")"
            echo "🔢 Current timestamp: $NOW_MS"
            echo "🔢 Hour ago timestamp: $HOUR_AGO_MS"
            echo "📅 Time range: From $HOUR_AGO_MS to $NOW_MS"

            # Search for the alert by its numerical ID
            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/events" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -G \
                --data-urlencode "filter[from]=$HOUR_AGO_MS" \
                --data-urlencode "filter[to]=$NOW_MS" \
                --data-urlencode "filter[query]=*")

            # Find the specific alert by its evt.id
            EVENT=$(echo "$RESPONSE" | jq --arg aid "$alert_id" '.data[] | select(.attributes.attributes.evt.id == $aid)')

            if [ -z "$EVENT" ]; then
                echo "Error: Could not find alert with ID $alert_id"
                exit 1
            fi

            echo "=== Alert Details ==="
            echo "$EVENT" | jq -r '
                "Event ID: \(.attributes.attributes.evt.id)\n" +
                "Title: \(.attributes.attributes.title // "N/A")\n" +
                "Message: \(.attributes.message // "N/A")\n" +
                "Status: \(.attributes.attributes.status // "N/A")\n" +
                "Service: \(.attributes.attributes.service // "N/A")\n" +
                "Timestamp: \(.attributes.attributes.timestamp // "N/A")\n" +
                "\nMonitor Details:" +
                "\n  Name: \(.attributes.attributes.monitor.name // "N/A")" +
                "\n  ID: \(.attributes.attributes.monitor.id // "N/A")" +
                "\n  Query: \(.attributes.attributes.monitor.query // "N/A")" +
                "\n  Type: \(.attributes.attributes.monitor.type // "N/A")" +
                "\n  Priority: \(.attributes.attributes.monitor.priority // "N/A")" +
                "\n  Created: \(.attributes.attributes.monitor.created_at // "N/A")" +
                "\n  Modified: \(.attributes.attributes.monitor.modified // "N/A")" +
                "\n\nThresholds:" +
                "\n  Critical: \(.attributes.attributes.monitor.options.thresholds.critical // "N/A")" +
                "\n\nLinks:" +
                "\n  Alert: https://us5.datadoghq.com\(.attributes.attributes.monitor.result.alert_url // "N/A")" +
                "\n  Logs: https://us5.datadoghq.com\(.attributes.attributes.monitor.result.logs_url // "N/A")" +
                "\n\nTags: \(.attributes.tags // [] | join(", ") // "N/A")"
            '
            """,
            args=[
                Arg(name="alert_id", description="Numerical ID of the alert event", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_alert_history(self) -> DatadogTool:
        """Get historical alert events for a monitor."""
        return DatadogTool(
            name="get_alert_history",
            description="Get historical alert events for a specific monitor",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_id" ]; then
                echo "Error: Monitor ID is required"
                exit 1
            fi

            # Default to last 24 hours if not specified
            HOURS=${hours:-24}
            FROM_TS=$(($(date +%s) - HOURS * 3600))

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/events" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -G \
                -d "filter=monitor_id:$monitor_id" \
                -d "from=$FROM_TS")

            echo "=== Alert History (Last $HOURS hours) ==="
            echo "$RESPONSE" | jq -r '.data[] | 
                "Time: \(.attributes.timestamp)\n" +
                "Status: \(.attributes.status)\n" +
                "Message: \(.attributes.message)\n" +
                "---"'
            """,
            args=[
                Arg(name="monitor_id", description="ID of the monitor", required=True),
                Arg(name="hours", description="Number of hours of history to retrieve", required=False)
            ],
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


    def query_alert_logs(self) -> DatadogTool:
        """Query logs related to an alert."""
        return DatadogTool(
            name="query_alert_logs",
            description="Query logs related to a specific alert or service",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$service" ]; then
                echo "Error: Service name is required"
                exit 1
            fi

            QUERY="service:$service"
            if [ ! -z "$status" ]; then
                QUERY="$QUERY status:$status"
            fi

            TIME_RANGE=${minutes:-60}
            FROM_TS=$(($(date +%s) - TIME_RANGE * 60))

            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -d '{
                    "filter": {
                        "from": "'"$FROM_TS"'",
                        "to": "now",
                        "query": "'"$QUERY"'"
                    },
                    "sort": "timestamp",
                    "page": {
                        "limit": 20
                    }
                }')

            echo "=== Log Results ==="
            echo "$RESPONSE" | jq -r '
                "Found \(.meta.page.total // 0) logs\n" +
                (.data[] | 
                    "Time: \(.attributes.timestamp)\n" +
                    "Status: \(.attributes.status)\n" +
                    "Message: \(.attributes.message)\n" +
                    "---")'
            """,
            args=[
                Arg(name="service", description="Service name to query", required=True),
                Arg(name="status", description="Status to filter by (e.g., error, warn)", required=False),
                Arg(name="minutes", description="Minutes of history to query (default: 60)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_alert_by_name(self) -> DatadogTool:
        """Search for recent alerts by monitor name."""
        return DatadogTool(
            name="get_alert_by_name",
            description="Search for recent DataDog alerts by monitor name",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_name" ]; then
                echo "Error: Monitor name is required"
                exit 1
            fi

            echo "🔍 Searching for alerts with monitor name: $monitor_name"

            # Get current timestamp and 1 hour ago in milliseconds
            NOW_MS=$(date +%s)000
            HOUR_AGO_MS=$(( $(date +%s) - 3600 ))000
            
            # Debug time info
            echo "🕒 Current time: $(date)"
            echo "🕐 Hour ago: $(date -d "@$(( $(date +%s) - 3600 ))")"
            echo "🔢 Current timestamp: $NOW_MS"
            echo "🔢 Hour ago timestamp: $HOUR_AGO_MS"
            echo "📅 Time range: From $HOUR_AGO_MS to $NOW_MS"

            # Escape the monitor name for the query
            ESCAPED_NAME=$(echo "$monitor_name" | sed 's/"/\\"/g')
            echo "🔒 Escaped monitor name: $ESCAPED_NAME"

            echo "📡 Making API request..."
            QUERY="*$ESCAPED_NAME*"
            echo "🔍 Query filter: $QUERY"

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/events" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -G \
                --data-urlencode "filter[from]=$HOUR_AGO_MS" \
                --data-urlencode "filter[to]=$NOW_MS" \
                --data-urlencode "filter[query]=$QUERY")

            echo "📥 Raw API Response:"
            echo "$RESPONSE" | jq '.'

            # Check if response is valid JSON
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "❌ Error: Invalid JSON response from API"
                echo "Raw response: $RESPONSE"
                exit 1
            fi

            echo "🔢 Total events in response:"
            echo "$RESPONSE" | jq '.data | length'

            echo "🔍 Filtering events for monitor name..."
            FILTERED_DATA=$(echo "$RESPONSE" | jq -r --arg name "$monitor_name" '.data[] | 
                select(.attributes.attributes.monitor.name != null) |
                select(.attributes.attributes.monitor.name | contains($name))')

            echo "📋 Filtered Data (raw):"
            echo "$FILTERED_DATA"

            if [ -z "$FILTERED_DATA" ]; then
                echo "❌ No alerts found matching monitor name: $monitor_name"
                exit 0
            fi

            echo "✅ Found matching alerts. Processing results..."
            echo "=== Found Alerts ==="
            echo "$FILTERED_DATA" | jq -r '
                "ID: \(.attributes.attributes.evt.id)\n" +
                "Monitor Name: \(.attributes.attributes.monitor.name // "N/A")\n" +
                "Title: \(.attributes.attributes.title // "N/A")\n" +
                "Status: \(.attributes.attributes.status // "N/A")\n" +
                "Timestamp: \(.attributes.date_happened // "N/A")\n" +
                "Service: \(.attributes.attributes.service // "N/A")\n" +
                "---"'
            """,
            args=[
                Arg(name="monitor_name", description="Name of the monitor to search for", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )
    
# Initialize tools
AlertTools() 