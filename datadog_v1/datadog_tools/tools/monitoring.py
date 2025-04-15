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
            print(f"❌ Failed to register Datadog monitoring tools: {str(e)}", file=sys.stderr)
            raise

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

            # Get current timestamp and 1 hour ago in milliseconds
            NOW_MS=$(date +%s)000
            HOUR_AGO_MS=$(($(date +%s) - 3600))000

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v2/events" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -G \
                --data-urlencode "filter[from]=$HOUR_AGO_MS" \
                --data-urlencode "filter[to]=$NOW_MS" \
                --data-urlencode "filter[query]=monitor:*\\"$monitor_name\\"*")

            # Check if response contains events
            if [ "$(echo "$RESPONSE" | jq '.data')" = "null" ]; then
                echo "No alerts found matching monitor name: $monitor_name"
                exit 0
            fi

            echo "=== Found Alerts ==="
            echo "$RESPONSE" | jq -r '.data[] | select(.attributes.attributes.monitor.name != null) | 
                "ID: \(.id)",
                "Monitor Name: \(.attributes.attributes.monitor.name // "N/A")",
                "Title: \(.attributes.attributes.title // "N/A")",
                "Status: \(.attributes.attributes.status // "N/A")",
                "Timestamp: \(.attributes.date_happened // "N/A")",
                "Service: \(.attributes.attributes.service // "N/A")",
                "---"
            '
            """,
            args=[
                Arg(name="monitor_name", description="Name of the monitor to search for", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize tools
MonitoringTools()
