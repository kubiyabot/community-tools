from kubiya_sdk.tools import Arg
from ..base import HoneycombTool
from kubiya_sdk.tools.registry import tool_registry

analyze_traces = HoneycombTool(
    name="analyze_traces",
    description="Query Honeycomb for trace stats like P99 and error rate for a given service",
    content="""
# Ensure required arguments are set
if [ -z "$dataset" ] || [ -z "$service_name" ] || [ -z "$start_time" ]; then
  echo '{"error": "Missing required arguments: dataset, service_name, or start_time"}'
  exit 1
fi

# Calculate time range
END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
START_TIME=$(date -u -d "$start_time minutes ago" +"%Y-%m-%dT%H:%M:%SZ")

# Build simple Honeycomb query
read -r -d '' QUERY <<EOF
{
  "calculations": [
    { "op": "P99", "column": "duration_ms" },
    { "op": "COUNT" },
    { "op": "AVG", "column": "duration_ms" }
  ],
  "filter": [
    { "column": "service_name", "op": "equals", "value": "$service_name" }
  ],
  "time_range": {
    "start": "$START_TIME",
    "end": "$END_TIME"
  }
}
EOF

# Send request to Honeycomb
RESPONSE=$(curl -s -X POST \
  -H "X-Honeycomb-Team: $HONEYCOMB_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$QUERY" \
  "https://api.honeycomb.io/1/query/$dataset")

# Validate response
if echo "$RESPONSE" | grep -q "error"; then
  echo "$RESPONSE"
  exit 1
fi

# Wrap result with service metadata
echo "$RESPONSE" | jq --arg service "$service_name" --arg start "$START_TIME" --arg end "$END_TIME" '{
  service: $service,
  time_range: { start: $start, end: $end },
  results: .
}'
""",
    args=[
        Arg(name="dataset", type="str", description="Honeycomb dataset name (e.g. 'test')", required=True),
        Arg(name="service_name", type="str", description="The name of the service to analyze", required=True),
        Arg(name="start_time", type="int", description="Minutes to look back from now (e.g. 30)", required=True)
    ]
)

tool_registry.register("honeycomb", analyze_traces)
