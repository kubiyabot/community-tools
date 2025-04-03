from kubiya_sdk.tools import Arg
from ..base import HoneycombTool
from kubiya_sdk.tools.registry import tool_registry
import sys
import os
import json
import requests
from datetime import datetime, timedelta

analyze_traces = HoneycombTool(
    name="analyze_traces",
    description="Query Honeycomb for trace stats like P99 and error rate for a given service",
    content="""
def validate_honeycomb_connection():
    if not os.getenv('HONEYCOMB_API_KEY'):
        return json.dumps({"error": "HONEYCOMB_API_KEY environment variable is not set"})
    return None

def calculate_time_range(minutes_ago: int) -> tuple[str, str]:
    now = datetime.utcnow()
    start_time = now - timedelta(minutes=minutes_ago)
    return (
        start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

def make_honeycomb_request(url: str, data: dict) -> dict:
    headers = {
        'X-Honeycomb-Team': os.getenv('HONEYCOMB_API_KEY'),
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Validate required arguments
if not all([dataset, service_name, start_time]):
    print(json.dumps({"error": "Missing required arguments: dataset, service_name, or start_time"}))
    sys.exit(1)

# Validate Honeycomb connection
error = validate_honeycomb_connection()
if error:
    print(error)
    sys.exit(1)

# Calculate time range
start_time_str, end_time_str = calculate_time_range(int(start_time))

# Build Honeycomb query
query = {
    "calculations": [
        {"op": "P99", "column": "duration_ms"},
        {"op": "COUNT"},
        {"op": "AVG", "column": "duration_ms"}
    ],
    "filter": [
        {"column": "service_name", "op": "equals", "value": service_name}
    ],
    "time_range": {
        "start": start_time_str,
        "end": end_time_str
    }
}

# Send request to Honeycomb
response = make_honeycomb_request(
    f"https://api.honeycomb.io/1/query/{dataset}",
    query
)

# Output response
print(json.dumps(response))
""",
    args=[
        Arg(name="dataset", type="str", description="Honeycomb dataset name (e.g. 'test')", required=True),
        Arg(name="service_name", type="str", description="The name of the service to analyze", required=True),
        Arg(name="start_time", type="int", description="Minutes to look back from now (e.g. 30)", required=True)
    ]
)

tool_registry.register("honeycomb", analyze_traces)
