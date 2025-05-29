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
                self.export_query(),
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

    def export_query(self) -> ObserveTool:
        """Export data from Observe using the meta/export/query endpoint."""
        return ObserveTool(
            name="observe_export_query",
            description="Export data from Observe using the meta export query endpoint with custom pipeline stages",
            content="""
            apk add -q --no-cache jq curl

            dataset_id="$OBSERVE_DATASET_ID"

            # Set default pipeline if not provided
            if [ -z "$pipeline" ]; then
                pipeline="pick_col timestamp, log | limit 100"
                echo "Using default pipeline: $pipeline"
            fi

            # Set default input_name if not provided
            if [ -z "$input_name" ]; then
                input_name="system"
                echo "Using default input_name: $input_name"
            fi

            # Set default stage_id if not provided
            if [ -z "$stage_id" ]; then
                stage_id="main"
                echo "Using default stage_id: $stage_id"
            fi

            # Set default interval if not provided
            if [ -z "$interval" ]; then
                interval="1h"
                echo "Using default interval: $interval"
            fi

            echo "Exporting data from Observe..."
            echo "Customer ID: $OBSERVE_CUSTOMER_ID"
            echo "Dataset ID: $dataset_id"
            echo "Input Name: $input_name"
            echo "Stage ID: $stage_id"
            echo "Pipeline: $pipeline"
            echo "Interval: $interval"
            
            # Build the JSON payload
            JSON_PAYLOAD=$(jq -n \
                --arg input_name "$input_name" \
                --arg dataset_id "$dataset_id" \
                --arg stage_id "$stage_id" \
                --arg pipeline "$pipeline" \
                '{
                    "query": {
                        "stages": [
                            {
                                "input": [
                                    {
                                        "inputName": $input_name,
                                        "datasetId": $dataset_id
                                    }
                                ],
                                "stageID": $stage_id,
                                "pipeline": $pipeline
                            }
                        ]
                    }
                }')

            echo "JSON Payload:"
            echo "$JSON_PAYLOAD" | jq '.'
            echo "============================================="
            
            # Call Observe API export endpoint
            RESPONSE=$(curl -s -X POST "https://$OBSERVE_CUSTOMER_ID.observeinc.com/v1/meta/export/query?interval=$interval" \
                -H "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_ACCESS_KEY" \
                -H "Content-Type: application/json" \
                -H "Accept: application/x-ndjson" \
                -d "$JSON_PAYLOAD")

            # Check if response is empty
            if [ -z "$RESPONSE" ]; then
                echo "No data returned from export query."
                exit 0
            fi

            echo "Export query results:"
            echo "============================================="
            
            # Process NDJSON response - each line is a separate JSON object
            echo "$RESPONSE" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    echo "$line" | jq '.'
                    echo "---------------------------------------------"
                fi
            done
            
            echo ""
            echo "Export query completed successfully."
            """,
            args=[
                Arg(name="pipeline", description="OPAL pipeline query to execute (e.g., 'pick_col timestamp, log | limit 100')", required=False),
                Arg(name="input_name", description="Input name for the query stage (default: 'system')", required=False),
                Arg(name="stage_id", description="Stage ID for the query (default: 'main')", required=False),
                Arg(name="interval", description="Time interval for the query (default: '1h')", required=False)
            ],
            image="alpine:latest"
        )

# Initialize tools
ObserveMonitoringTools()
