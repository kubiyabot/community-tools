from typing import List
import sys
from .base import DatadogTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class MonitoringTools:
    """Datadog monitoring and analysis tools."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Create and register tools
            tools = [
                self.get_alert_details(),
                self.compare_error_rates(),
                self.query_logs(),
                self.get_metrics()
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
        """Get details about a specific alert/incident."""
        return DatadogTool(
            name="datadog_alert_details",
            description="Get detailed information about a specific alert",
            content="""
            # Install jq if not present
            apk add --no-cache jq

            # Validate connection and inputs
            validate_datadog_connection

            if [ -z "$alert_id" ]; then
                echo "Error: Alert ID is required"
                exit 1
            fi

            echo "=== Alert Details ==="
            
            # Get alert information
            ALERT_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor/$alert_id" \
                -H "DD-API-KEY: $DD_API_KEY" \
                -H "DD-APPLICATION-KEY: $DD_APP_KEY")

            # Check for errors and format output
            echo "$ALERT_DATA" | jq -r '
                if .errors then
                    ["Error retrieving alert:"] + .errors | .[]
                elif .id then
                    "ID: \(.id)",
                    "Name: \(.name // "N/A")",
                    "Status: \(.overall_state // "N/A")",
                    "Type: \(.type // "N/A")",
                    "Query: \(.query // "N/A")",
                    "Message: \(.message // "N/A")",
                    "Created: \(.created | strftime("%Y-%m-%d %H:%M:%S") // "N/A")",
                    "Modified: \(.modified | strftime("%Y-%m-%d %H:%M:%S") // "N/A")",
                    "",
                    "=== Options ===",
                    (.options | to_entries[] | "\(.key): \(.value)")
                else
                    "No alert found with ID: '$alert_id'"
                end'

            # Get recent alert history if requested
            if [ "$include_history" = "true" ]; then
                echo -e "\n=== Alert History ==="
                HISTORY_DATA=$(curl -s -X GET "https://api.$DD_SITE/api/v1/monitor/$alert_id/history" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY")

                echo "$HISTORY_DATA" | jq -r '
                    if .errors then
                        ["Error retrieving history:"] + .errors | .[]
                    elif length > 0 then
                        .[] | [
                            (.date_happened | strftime("%Y-%m-%d %H:%M:%S")),
                            "Status: \(.status // "N/A")",
                            "Message: \(.message // "N/A")"
                        ] | .[]
                    else
                        "No history found"
                    end'
            fi
            """,
            args=[
                Arg(name="alert_id",
                    description="ID of the alert to analyze",
                    required=True),
                Arg(name="include_history",
                    description="Include alert history",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def compare_error_rates(self) -> DatadogTool:
        """Compare error rates between time periods."""
        return DatadogTool(
            name="compare_error_rates",
            description="Compare error rates between current and previous periods",
            content="""
            # Install jq and date tools
            apk add --no-cache jq coreutils

            # Validate connection
            validate_datadog_connection

            # Calculate time periods
            NOW=$(date +%s)
            WEEK_AGO=$((NOW - 604800))
            TWO_WEEKS_AGO=$((WEEK_AGO - 604800))

            # URL encode the metric query
            ENCODED_QUERY=$(echo "$metric_query" | jq -sRr @uri)

            echo "=== Error Rate Comparison ==="
            echo "Query: $metric_query"

            # Function to fetch and process metrics
            fetch_metrics() {
                local start=$1
                local end=$2
                local period="$3"
                
                echo "\n$period:"
                curl -s -X GET "https://api.$DD_SITE/api/v1/query/metrics?from=$start&to=$end&query=$ENCODED_QUERY" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" | \
                    jq -r '
                        if .errors then
                            .errors[] | "Error: \(.)" 
                        elif .series == null or (.series | length == 0) then
                            "No data found for this period"
                        else
                            .series[0].pointlist | 
                            map(.[1]) | 
                            (add / length | "Average: \(. | tostring)"), 
                            ("Total: \(add | tostring)")
                        end'
            }

            # Get current week's data
            fetch_metrics "$WEEK_AGO" "$NOW" "Current Week"

            # Get previous week's data
            fetch_metrics "$TWO_WEEKS_AGO" "$WEEK_AGO" "Previous Week"

            # If detailed analysis requested, show hourly breakdown
            if [ "$detailed_analysis" = "true" ]; then
                echo "\n=== Hourly Breakdown ==="
                curl -s -X GET "https://api.$DD_SITE/api/v1/query/metrics?from=$WEEK_AGO&to=$NOW&query=$ENCODED_QUERY" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" | \
                    jq -r '
                        if .series then
                            .series[0].pointlist[] | 
                            "\(.[0] | todate | strftime("%Y-%m-%d %H:00")): \(.[1])"
                        else
                            "No data available for detailed analysis"
                        end' | sort
            fi
            """,
            args=[
                Arg(name="metric_query",
                    description="Custom metric query for error rate",
                    required=True),
                Arg(name="detailed_analysis",
                    description="Show detailed hourly breakdown",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def query_logs(self) -> DatadogTool:
        """Query and analyze logs."""
        return DatadogTool(
            name="query_logs",
            description="Query and analyze Datadog logs",
            content="""
            # Install required tools
            apk add --no-cache jq coreutils

            # Validate connection
            validate_datadog_connection

            # Set time range
            NOW=$(date +%s)
            if [ -z "$time_range" ]; then
                time_range="1h"
            fi
            
            # Convert time range to seconds
            case $time_range in
                "1h") FROM=$((NOW - 3600));;
                "6h") FROM=$((NOW - 21600));;
                "1d") FROM=$((NOW - 86400));;
                "7d") FROM=$((NOW - 604800));;
                *) FROM=$((NOW - 3600));; # Default to 1h
            esac

            echo "=== Log Analysis ==="
            echo "Time Range: $time_range"
            echo "Query: ${query:-*}"

            # Get logs
            get_logs "${query:-*}" "$FROM" "$NOW" | \
                jq '.logs[] | {
                    timestamp: .attributes.timestamp,
                    service: .attributes.service,
                    status: .attributes.status,
                    message: .attributes.message
                }'

            # If pattern analysis requested, show common patterns
            if [ "$analyze_patterns" = "true" ]; then
                echo "\n=== Common Patterns ==="
                get_logs "${query:-*}" "$FROM" "$NOW" | \
                    jq -r '.logs[].attributes.message' | \
                    sort | uniq -c | sort -nr | head -10
            fi
            """,
            args=[
                Arg(name="query",
                    description="Log query string",
                    required=False),
                Arg(name="time_range",
                    description="Time range (1h, 6h, 1d, 7d)",
                    required=False),
                Arg(name="analyze_patterns",
                    description="Analyze common patterns",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_metrics(self) -> DatadogTool:
        """Get and analyze metrics."""
        return DatadogTool(
            name="get_metrics",
            description="Get and analyze Datadog metrics",
            content="""
            # Install required tools
            apk add --no-cache jq coreutils

            # Validate connection
            validate_datadog_connection

            # Set time range
            NOW=$(date +%s)
            if [ -z "$time_range" ]; then
                time_range="1h"
            fi
            
            # Convert time range to seconds
            case $time_range in
                "1h") FROM=$((NOW - 3600));;
                "6h") FROM=$((NOW - 21600));;
                "1d") FROM=$((NOW - 86400));;
                "7d") FROM=$((NOW - 604800));;
                *) FROM=$((NOW - 3600));; # Default to 1h
            esac

            echo "=== Metric Analysis ==="
            echo "Time Range: $time_range"
            echo "Query: ${metric_query}"

            # Get metrics
            METRIC_DATA=$(query_metrics "${metric_query}" "$FROM" "$NOW")

            # Basic statistics
            echo "\n=== Basic Statistics ==="
            echo "$METRIC_DATA" | \
                jq '.series[0].pointlist[] | .[1]' | \
                awk '
                    BEGIN { print "Calculating..." }
                    {
                        sum += $1
                        sumsq += ($1)^2
                        if (NR == 1 || $1 < min) min = $1
                        if (NR == 1 || $1 > max) max = $1
                    }
                    END {
                        print "Count:", NR
                        print "Min:", min
                        print "Max:", max
                        print "Average:", sum/NR
                        print "StdDev:", sqrt(sumsq/NR - (sum/NR)^2)
                    }'

            # If aggregation requested, show by specified dimension
            if [ ! -z "$aggregate_by" ]; then
                echo "\n=== Aggregation by $aggregate_by ==="
                echo "$METRIC_DATA" | \
                    jq --arg dim "$aggregate_by" \
                    '.series[] | select(.scope | contains([$dim])) | 
                    {dimension: .scope[], avg: (.pointlist | map(.[1]) | add / length)}'
            fi
            """,
            args=[
                Arg(name="metric_query",
                    description="Metric query string",
                    required=True),
                Arg(name="time_range",
                    description="Time range (1h, 6h, 1d, 7d)",
                    required=False),
                Arg(name="aggregate_by",
                    description="Dimension to aggregate by",
                    required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize when module is imported
MonitoringTools() 