from typing import List
import sys
from .base import DatadogTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class MonitorTools:
    """Tools for managing Datadog monitors."""

    def __init__(self):
        """Initialize and register monitor management tools."""
        try:
            tools = [
                self.list_all_monitors(),
                self.get_monitor_details(),
                self.mute_monitor(),
                self.unmute_monitor(),
                self.search_monitors(),
                self.update_monitor()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("datadog", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Datadog monitor tools: {str(e)}", file=sys.stderr)
            raise

    def list_all_monitors(self) -> DatadogTool:
        """List all Datadog monitors."""
        return DatadogTool(
            name="list_monitors",
            description="List all Datadog monitors with their current status",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            echo "$RESPONSE" | jq -r '.[] | 
                "=== Monitor ===\n" +
                "ID: \(.id)\n" +
                "Name: \(.name)\n" +
                "Status: \(.overall_state)\n" +
                "Type: \(.type)\n" +
                "Priority: \(.priority // "None")\n" +
                "Tags: \(.tags // [] | join(", "))\n" +
                "---"'
            """,
            args=[],
            image="curlimages/curl:8.1.2"
        )

    def search_monitors(self) -> DatadogTool:
        """Search monitors by name, tags, or status."""
        return DatadogTool(
            name="search_monitors",
            description="Search Datadog monitors using various filters",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            QUERY_PARAMS=""
            
            if [ ! -z "$name" ]; then
                QUERY_PARAMS="$QUERY_PARAMS&name=$name"
            fi
            
            if [ ! -z "$tags" ]; then
                QUERY_PARAMS="$QUERY_PARAMS&tags=$tags"
            fi
            
            if [ ! -z "$status" ]; then
                QUERY_PARAMS="$QUERY_PARAMS&status=$status"
            fi

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor?${QUERY_PARAMS#&}" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            echo "$RESPONSE" | jq -r '.[] | 
                "=== Monitor ===\n" +
                "ID: \(.id)\n" +
                "Name: \(.name)\n" +
                "Status: \(.overall_state)\n" +
                "Type: \(.type)\n" +
                "Priority: \(.priority // "None")\n" +
                "Tags: \(.tags // [] | join(", "))\n" +
                "---"'
            """,
            args=[
                Arg(name="name", description="Search by monitor name", required=False),
                Arg(name="tags", description="Search by monitor tags (comma-separated)", required=False),
                Arg(name="status", description="Filter by status (OK, Alert, Warn, No Data)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_monitor_details(self) -> DatadogTool:
        """Get detailed information about a specific monitor."""
        return DatadogTool(
            name="get_monitor_details",
            description="Get detailed information about a specific Datadog monitor",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_id" ]; then
                echo "Error: Monitor ID is required"
                exit 1
            fi

            RESPONSE=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor/$monitor_id" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            echo "$RESPONSE" | jq -r '
                "=== Monitor Details ===\n" +
                "ID: \(.id)\n" +
                "Name: \(.name)\n" +
                "Status: \(.overall_state)\n" +
                "Type: \(.type)\n" +
                "Query: \(.query)\n" +
                "Message: \(.message)\n" +
                "Priority: \(.priority // "None")\n" +
                "Creator: \(.creator.name)\n" +
                "Created: \(.created)\n" +
                "Modified: \(.modified)\n" +
                "Options:\n" +
                "  Notify on No Data: \(.options.notify_no_data)\n" +
                "  Notify on Resolved: \(.options.notify_audit)\n" +
                "  Timeout (hrs): \(.options.timeout_h // "None")\n" +
                "Tags: \(.tags // [] | join(", "))"
            '
            """,
            args=[
                Arg(name="monitor_id", description="ID of the monitor to get details for", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

    def mute_monitor(self) -> DatadogTool:
        """Mute a specific monitor."""
        return DatadogTool(
            name="mute_monitor",
            description="Mute a specific Datadog monitor",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_id" ]; then
                echo "Error: Monitor ID is required"
                exit 1
            fi

            END_TIME=""
            if [ ! -z "$duration_hours" ]; then
                END_TIME=$(($(date +%s) + duration_hours * 3600))
            fi

            DATA="{}"
            if [ ! -z "$END_TIME" ]; then
                DATA="{\\\"end\\\": $END_TIME}"
            fi

            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v1/monitor/$monitor_id/mute" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -d "$DATA")

            echo "$RESPONSE" | jq -r '
                if .errors then
                    "Error: \(.errors[])"
                else
                    "Successfully muted monitor \(.id)"
                end'
            """,
            args=[
                Arg(name="monitor_id", description="ID of the monitor to mute", required=True),
                Arg(name="duration_hours", description="Duration to mute in hours (optional)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def unmute_monitor(self) -> DatadogTool:
        """Unmute a specific monitor."""
        return DatadogTool(
            name="unmute_monitor",
            description="Unmute a specific Datadog monitor",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_id" ]; then
                echo "Error: Monitor ID is required"
                exit 1
            fi

            RESPONSE=$(curl -s -X POST "https://api.$DD_SITE/api/v1/monitor/$monitor_id/unmute" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            echo "$RESPONSE" | jq -r '
                if .errors then
                    "Error: \(.errors[])"
                else
                    "Successfully unmuted monitor \(.id)"
                end'
            """,
            args=[
                Arg(name="monitor_id", description="ID of the monitor to unmute", required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

    def update_monitor(self) -> DatadogTool:
        """Update monitor properties."""
        return DatadogTool(
            name="update_monitor",
            description="Update properties of an existing Datadog monitor",
            content="""
            apk add --no-cache jq
            validate_datadog_connection

            if [ -z "$monitor_id" ]; then
                echo "Error: Monitor ID is required"
                exit 1
            fi

            # Build update payload
            PAYLOAD="{"
            if [ ! -z "$name" ]; then
                PAYLOAD="$PAYLOAD\\\"name\\\":\\\"$name\\\","
            fi
            if [ ! -z "$message" ]; then
                PAYLOAD="$PAYLOAD\\\"message\\\":\\\"$message\\\","
            fi
            if [ ! -z "$priority" ]; then
                PAYLOAD="$PAYLOAD\\\"priority\\\":\\\"$priority\\\","
            fi
            PAYLOAD="${PAYLOAD%,}}"

            RESPONSE=$(curl -s -X PUT "https://api.$DD_SITE/api/v1/monitor/$monitor_id" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                -H "Content-Type: application/json" \
                -d "$PAYLOAD")

            echo "$RESPONSE" | jq -r '
                if .errors then
                    "Error: \(.errors[])"
                else
                    "Successfully updated monitor \(.id)"
                end'
            """,
            args=[
                Arg(name="monitor_id", description="ID of the monitor to update", required=True),
                Arg(name="name", description="New name for the monitor", required=False),
                Arg(name="message", description="New message/description for the monitor", required=False),
                Arg(name="priority", description="New priority level (low, normal, high)", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize tools
MonitorTools() 