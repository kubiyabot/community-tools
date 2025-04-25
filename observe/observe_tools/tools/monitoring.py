from typing import List
import sys
from .base import ObserveTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class ObserveMonitoringTools:
    """Observe platform monitoring and analysis tools."""

    def __init__(self):
        """Initialize and register Observe monitoring tools."""
        try:
            tools = [
                self.fetch_logs(),
                self.query_metrics(),
                self.get_alert_details(),
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("observe", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Observe monitoring tools: {str(e)}", file=sys.stderr)
            raise

    def fetch_logs(self) -> ObserveTool:
        """Fetch logs from Observe based on query parameters."""
        return ObserveTool(
            name="observe_fetch_logs",
            description="Fetch logs from Observe platform with flexible query parameters",
            content="""
            apk add -q --no-cache jq curl

            # Validate required environment variables
            validate_observe_auth

            # Validate required parameters
            if [ -z "$dataset_id" ]; then
                echo "Error: dataset_id is required"
                exit 1
            fi

            # Format timestamps with helper function
            if [ -n "$start_time" ]; then
                start_time=$(format_timestamp "$start_time")
            else
                start_time=$(format_timestamp)
                echo "Using default start time: $start_time (now)"
            fi

            if [ -n "$end_time" ]; then
                end_time=$(format_timestamp "$end_time")
            else
                end_time=$(format_timestamp)
                echo "Using default end time: $end_time (now)"
            fi

            # Set default limit if not provided
            if [ -z "$limit" ]; then
                limit=100
                echo "Using default limit: $limit"
            fi

            echo "Fetching logs from Observe..."
            echo "Dataset ID: $dataset_id"
            echo "Time range: $start_time to $end_time"
            if [ -n "$filter" ]; then
                echo "Filter: $filter"
            fi
            
            # Use the helper function to get events
            RESPONSE=$(get_events "$dataset_id" "$start_time" "$end_time" "$filter" "$limit")

            # Format and display the results
            EVENTS=$(echo "$RESPONSE" | jq -r '.events')
            EVENT_COUNT=$(echo "$EVENTS" | jq -r 'length')

            if [ "$EVENT_COUNT" -eq 0 ]; then
                echo "No logs found matching the criteria."
                exit 0
            fi

            echo "Found $EVENT_COUNT log entries:"
            echo "============================================="
            
            echo "$EVENTS" | jq -r '.[] | "Timestamp: \(.timestamp)", "Resource ID: \(.resource_id // \"N/A\")", "Labels: \(.labels | tostring)", "Fields: \(.fields | tostring)", "============================================="'
            
            echo ""
            echo "Log query completed successfully."
            """,
            args=[
                Arg(name="dataset_id", description="The ID of the Observe dataset to query", required=True),
                Arg(name="start_time", description="Start time in ISO 8601 format (e.g., 2023-01-01T00:00:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO 8601 format (e.g., 2023-01-01T01:00:00Z)", required=False),
                Arg(name="filter", description="OPAL filter expression to filter the logs", required=False),
                Arg(name="limit", description="Maximum number of log entries to return", required=False)
            ],
            image="alpine:latest"
        )
        
    def query_metrics(self) -> ObserveTool:
        """Query metrics from Observe datasets with OPAL queries."""
        return ObserveTool(
            name="observe_query_metrics",
            description="Query metrics and insights from Observe platform datasets with OPAL queries",
            content="""
            apk add -q --no-cache jq curl
            
            # Validate authentication
            validate_observe_auth
            
            # Validate required parameters
            if [ -z "$dataset_id" ]; then
                echo "Error: dataset_id is required"
                exit 1
            fi
            
            if [ -z "$query" ]; then
                echo "Error: OPAL query is required"
                exit 1
            fi
            
            # Format timestamps
            if [ -n "$start_time" ]; then
                start_time=$(format_timestamp "$start_time")
            else
                # Default to 24 hours ago
                start_time=$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')
                echo "Using default start time: $start_time (24 hours ago)"
            fi
            
            if [ -n "$end_time" ]; then
                end_time=$(format_timestamp "$end_time")
            else
                end_time=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
                echo "Using default end time: $end_time (now)"
            fi
            
            echo "Running OPAL query on Observe dataset..."
            echo "Dataset ID: $dataset_id"
            echo "Time range: $start_time to $end_time"
            echo "Query: $query"
            
            # Use helper function to query the dataset
            RESPONSE=$(query_dataset "$dataset_id" "$query" "$start_time" "$end_time")
            
            # Parse and display results
            echo "Query executed successfully!"
            echo "============================================="
            
            # Check result format and render appropriately
            if echo "$RESPONSE" | jq -e '.results' > /dev/null; then
                # Time series or table data
                DATA_TYPE=$(echo "$RESPONSE" | jq -r '.type // "unknown"')
                COLUMNS=$(echo "$RESPONSE" | jq -r '.columns | length')
                ROWS=$(echo "$RESPONSE" | jq -r '.results | length')
                
                echo "Result type: $DATA_TYPE"
                echo "Columns: $COLUMNS"
                echo "Rows: $ROWS"
                echo "============================================="
                
                if [ "$DATA_TYPE" = "table" ]; then
                    # Table format - show headers and rows
                    HEADERS=$(echo "$RESPONSE" | jq -r '.columns | map(.name) | join("\t")')
                    echo -e "$HEADERS"
                    echo "---------------------------------------------"
                    echo "$RESPONSE" | jq -r '.results | .[] | map(.) | join("\t")' 
                elif [ "$DATA_TYPE" = "timeseries" ]; then
                    # Time series format - show timestamp and values
                    echo "$RESPONSE" | jq -r '.results | .[] | "Time: \(.[0])\tValue: \(.[1])"'
                else
                    # Generic format - just dump the JSON
                    echo "$RESPONSE" | jq '.results'
                fi
            else
                # Unknown format - just pretty print
                echo "$RESPONSE" | jq '.'
            fi
            
            echo "============================================="
            echo "Query complete."
            """,
            args=[
                Arg(name="dataset_id", description="The ID of the Observe dataset to query", required=True),
                Arg(name="query", description="OPAL query to execute against the dataset", required=True),
                Arg(name="start_time", description="Start time in ISO 8601 format (e.g., 2023-01-01T00:00:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO 8601 format (e.g., 2023-01-01T01:00:00Z)", required=False)
            ],
            image="alpine:latest"
        )
        
    def get_alert_details(self) -> ObserveTool:
        """Retrieve details about a specific alert from Observe."""
        return ObserveTool(
            name="observe_alert_details",
            description="Get detailed information about an alert from the Observe platform",
            content="""
            apk add -q --no-cache jq curl
            
            # Validate authentication
            validate_observe_auth
            
            # Validate required parameters
            if [ -z "$alert_id" ]; then
                echo "Error: alert_id is required"
                exit 1
            fi
            
            echo "Fetching alert details from Observe..."
            echo "Alert ID: $alert_id"
            
            # Use helper function to get alert details
            RESPONSE=$(get_alert "$alert_id")

            # Print alert details
            echo "============================================="
            echo "ALERT DETAILS"
            echo "============================================="
            
            # Extract relevant fields and format them
            echo "$RESPONSE" | jq -r '
                "ID: \(.id // "N/A")",
                "Name: \(.name // "N/A")",
                "Status: \(.status // "N/A")",
                "Severity: \(.severity // "N/A")",
                "Created: \(.created_at // "N/A")",
                "Updated: \(.updated_at // "N/A")",
                "Description: \(.description // "N/A")",
                "----------------------",
                "Monitor ID: \(.monitor_id // "N/A")",
                "Dataset ID: \(.dataset_id // "N/A")",
                "----------------------",
                "Associated Resources:",
                (.resources // [] | map("- \(.)") | join("\n")),
                "----------------------",
                "Alert URL: https://app.observeinc.com/alerts/\(.id // "N/A")"
            '
            
            # If the alert has a monitor, fetch monitor details
            MONITOR_ID=$(echo "$RESPONSE" | jq -r '.monitor_id // ""')
            
            if [ -n "$MONITOR_ID" ]; then
                echo ""
                echo "Fetching related monitor details..."
                
                MONITOR_RESPONSE=$(get_monitor "$MONITOR_ID")
                
                if ! echo "$MONITOR_RESPONSE" | jq -e '.error' > /dev/null; then
                    echo "============================================="
                    echo "MONITOR DETAILS"
                    echo "============================================="
                    
                    echo "$MONITOR_RESPONSE" | jq -r '
                        "ID: \(.id // "N/A")",
                        "Name: \(.name // "N/A")",
                        "Type: \(.type // "N/A")",
                        "Status: \(.status // "N/A")",
                        "Dataset: \(.dataset_name // "N/A")",
                        "Query: \(.query // "N/A")",
                        "----------------------",
                        "Monitor URL: https://app.observeinc.com/monitors/\(.id // "N/A")"
                    '
                else
                    echo "Unable to fetch monitor details."
                fi
            fi
            
            echo ""
            echo "Alert information retrieval complete."
            """,
            args=[
                Arg(name="alert_id", description="The ID of the alert to retrieve", required=True),
            ],
            image="alpine:latest"
        )

# Initialize tools
ObserveMonitoringTools()
