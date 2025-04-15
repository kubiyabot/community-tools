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
                self.query_alert_logs()
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
            description="Retrieve details of a specific alert event",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$alert_id" ]; then
                echo "Error: Alert ID is required"
                exit 1
            fi

            echo "Fetching details for alert ID: $alert_id"

            # First try to get recent monitor alerts
            NOW=$(date +%s)
            HOUR_AGO=$((NOW - 3600))

            MONITORS_RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            # Debug: Print monitors response
            echo "Debug - Found Monitors:"
            echo "$MONITORS_RESPONSE" | jq -r '.[] | select(.overall_state=="Alert") | .name'
            echo

            # Get details of all alerting monitors
            echo "=== Alert Details ==="
            echo "$MONITORS_RESPONSE" | jq -r '.[] | select(.overall_state=="Alert") | 
                "Monitor ID: \(.id)\n" +
                "Name: \(.name)\n" +
                "Message: \(.message // "N/A")\n" +
                "Query: \(.query // "N/A")\n" +
                "Status: \(.overall_state)\n" +
                "Last Triggered: \(.last_triggered_ts // "Unknown")\n" +
                "Priority: \(.priority // "None")\n" +
                "\nAlert Conditions:" +
                (if .options.thresholds then
                    "\n  Warning: \(.options.thresholds.warning // "N/A")" +
                    "\n  Critical: \(.options.thresholds.critical // "N/A")"
                else
                    "\n  N/A"
                end) +
                "\n\nNotification Settings:" +
                "\n  Notify No Data: \(.options.notify_no_data // false)" +
                "\n  Renotify Interval: \(.options.renotify_interval // "N/A")" +
                "\n\nTags: \(.tags // [] | join(", ") // "N/A")" +
                "\n---\n"
            '

            # Get state history for each alerting monitor
            echo "$MONITORS_RESPONSE" | jq -r '.[] | select(.overall_state=="Alert") | .id' | while read -r monitor_id; do
                if [ -n "$monitor_id" ]; then
                    echo "=== State History for Monitor $monitor_id ==="
                    STATE_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor/$monitor_id/states" \
                        -H "DD-API-KEY: $DD_API_KEY" \
                        -H "DD-APPLICATION-KEY: $DD_APP_KEY")

                    echo "$STATE_DATA" | jq -r '.[] | 
                        "Time: \(.entered_at)",
                        "State: \(.value)",
                        "---"
                    '
                    echo
                fi
            done
            """,
            args=[
                Arg(name="alert_id", description="ID of the alert event (optional - will show all current alerts if not specified)", required=False)
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
        """Compare error rates between time periods."""
        return DatadogTool(
            name="compare_error_rates",
            description="Compare error rates between current and previous periods",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$service" ]; then
                echo "Error: Service name is required"
                exit 1
            fi

            NOW_TS=$(date +%s)
            PERIOD_SEC=${period_hours:-24}
            PERIOD_SEC=$((PERIOD_SEC * 3600))
            PERIOD_AGO_TS=$((NOW_TS - PERIOD_SEC))
            TWO_PERIODS_AGO_TS=$((NOW_TS - (2 * PERIOD_SEC)))

            # Query current period
            CURRENT=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/analytics/aggregate" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -d '{
                    "filter": {
                        "from": '"$PERIOD_AGO_TS"',
                        "to": '"$NOW_TS"',
                        "query": "service:'"$service"' status:error"
                    },
                    "compute": [{"aggregation": "count"}]
                }')

            # Query previous period
            PREVIOUS=$(curl -s -X POST "https://api.$DD_SITE/api/v2/logs/analytics/aggregate" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -d '{
                    "filter": {
                        "from": '"$TWO_PERIODS_AGO_TS"',
                        "to": '"$PERIOD_AGO_TS"',
                        "query": "service:'"$service"' status:error"
                    },
                    "compute": [{"aggregation": "count"}]
                }')

            CURRENT_COUNT=$(echo "$CURRENT" | jq -r '.data.buckets[0].computes.c0 // 0')
            PREVIOUS_COUNT=$(echo "$PREVIOUS" | jq -r '.data.buckets[0].computes.c0 // 0')

            echo "=== Error Rate Comparison ==="
            echo "Service: $service"
            echo "Current period ($((PERIOD_SEC/3600))h): $CURRENT_COUNT errors"
            echo "Previous period ($((PERIOD_SEC/3600))h): $PREVIOUS_COUNT errors"
            
            if [ $PREVIOUS_COUNT -eq 0 ]; then
                if [ $CURRENT_COUNT -eq 0 ]; then
                    echo "No errors in either period"
                else
                    echo "∞% increase (no errors in previous period)"
                fi
            else
                PERCENT_CHANGE=$(( (CURRENT_COUNT - PREVIOUS_COUNT) * 100 / PREVIOUS_COUNT ))
                if [ $PERCENT_CHANGE -gt 0 ]; then
                    echo "⚠️ $PERCENT_CHANGE% increase in errors"
                elif [ $PERCENT_CHANGE -lt 0 ]; then
                    echo "✅ $((PERCENT_CHANGE * -1))% decrease in errors"
                else
                    echo "No change in error rate"
                fi
            fi
            """,
            args=[
                Arg(name="service", description="Service name to analyze", required=True),
                Arg(name="period_hours", description="Hours to compare (default: 24)", required=False)
            ],
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

# Initialize tools
AlertTools() 