from kubiya_sdk.tools import Arg
from ..base import HoneycombTool
from kubiya_sdk.tools.registry import tool_registry

analyze_traces = HoneycombTool(
    name="analyze_traces",
    description="Analyze traces in Honeycomb",
    content="""
        # Validate Honeycomb connection
        validate_honeycomb_connection

        # Parse arguments
        if [ -z "$dataset" ] || [ -z "$service_name" ] || [ -z "$start_time" ]; then
            echo "Error: Required arguments missing"
            exit 1
        fi

        # Calculate time range
        START_TIME=$(date -u -d "-${start_time} minutes" +"%Y-%m-%dT%H:%M:%SZ")
        END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # Build query JSON
        QUERY=$(cat <<EOF
{
    "calculations": [
        {"op": "P99", "column": "duration_ms"},
        {"op": "COUNT"},
        {"op": "RATE", "column": "error"}
    ],
    "filter": [
        {
            "column": "service_name",
            "op": "equals",
            "value": "$service_name"
        }
    ],
    "time_range": {
        "start": "$START_TIME",
        "end": "$END_TIME"
    }
}
EOF
)

        # Add additional filter if provided
        if [ ! -z "$filter_str" ]; then
            COLUMN=$(echo $filter_str | cut -d= -f1)
            VALUE=$(echo $filter_str | cut -d= -f2)
            QUERY=$(echo $QUERY | jq --arg col "$COLUMN" --arg val "$VALUE" '.filter += [{"column": $col, "op": "equals", "value": $val}]')
        fi

        # Make API request
        curl -s -X POST \
            -H "X-Honeycomb-Team: $HONEYCOMB_API_KEY" \
            -H "Content-Type: application/json" \
            -d "$QUERY" \
            "https://api.honeycomb.io/1/queries/$dataset" | jq '.'
    """,
    args=[
        Arg(name="dataset", type="str", description="Honeycomb dataset", required=True),
        Arg(name="service_name", type="str", description="Service name to analyze", required=True),
        Arg(name="start_time", type="int", description="Start time in minutes ago", required=True),
        Arg(name="filter_str", type="str", description="Additional filter in format 'column=value'", required=False),
    ]
)

tool_registry.register("honeycomb", analyze_traces) 


