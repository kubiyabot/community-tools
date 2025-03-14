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
                self.query_logs()
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

            fetch_logs() {
                local start_ts="$1"
                local end_ts="$2"
                local period_name="$3"

                echo "\n=== Fetching logs for $period_name ==="

                JSON_PAYLOAD=$(cat <<EOF
                {
                "filter": {
                    "from": $start_ts,
                    "to": $end_ts,
                    "query": "@service:$service @status:error"
                },
                "compute": [
                    { "aggregation": "count" }
                ],
                "group_by": [
                    { "facet": "@service" },
                    { "facet": "@status" }
                ]
                }
    EOF
                )

                RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/analytics/aggregate" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                    -H "Content-Type: application/json" \
                    --data-binary "$JSON_PAYLOAD")

                echo "Raw API Response:"
                echo "$RESPONSE" | jq

                ERROR_COUNT=$(echo "$RESPONSE" | jq -r '.data.buckets[0].computes.c0 // "0"')

                if [ "$ERROR_COUNT" -eq "0" ]; then
                    echo "No errors found for $period_name"
                else
                    echo "Total Errors in $period_name: $ERROR_COUNT"
                fi
            }

            fetch_logs "$(($(date +%s) - 604800))" "$(date +%s)" "Current Week"
            fetch_logs "$(($(date +%s) - 1209600))" "$(($(date +%s) - 604800))" "Previous Week"
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

# Initialize tools
MonitoringTools()
