from kubiya_sdk.tools import Arg
from ..base import HoneycombTool
from kubiya_sdk.tools.registry import tool_registry

analyze_traces = HoneycombTool(
    name="analyze_traces",
    description="Analyze traces in Honeycomb",
    content="""
import requests
import json
from datetime import datetime, timedelta

def analyze_traces(api_key, dataset, service_name, start_time):
    headers = {
        'X-Honeycomb-Team': api_key,
        'Content-Type': 'application/json'
    }
    
    query = {
        'calculations': [
            {'op': 'P99', 'column': 'duration_ms'},
            {'op': 'COUNT'}
        ],
        'filter': {
            'column': 'service.name',
            'op': 'equals',
            'value': service_name
        },
        'time_range': start_time
    }
    
    response = requests.post(
        f'https://api.honeycomb.io/1/queries/{dataset}',
        headers=headers,
        json=query
    )
    
    return response.json()

result = analyze_traces(api_key, dataset, service_name, start_time)
print(json.dumps(result, indent=2))
    """,
    args=[
        Arg(name="api_key", type="str", description="Honeycomb API key", required=True),
        Arg(name="dataset", type="str", description="Honeycomb dataset", required=True),
        Arg(name="service_name", type="str", description="Service name to analyze", required=True),
        Arg(name="start_time", type="int", description="Start time in minutes ago", required=True),
    ],
)

tool_registry.register("honeycomb", analyze_traces) 