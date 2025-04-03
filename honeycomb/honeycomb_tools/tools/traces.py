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

def analyze_traces(api_key, dataset, service_name, start_time, filters=None):
    headers = {
        'X-Honeycomb-Team': api_key,
        'Content-Type': 'application/json'
    }
    
    now = datetime.utcnow()
    start = now - timedelta(minutes=start_time)
    
    # Base query structure
    query = {
        'calculations': [
            {'op': 'P99', 'column': 'duration_ms'},
            {'op': 'COUNT'},
            {'op': 'RATE', 'column': 'error'},
            {'op': 'AVG', 'column': 'duration_ms'}
        ],
        'filter': [
            {
                'column': 'service_name',
                'op': 'equals',
                'value': service_name
            }
        ],
        'time_range': {
            'start': start.isoformat() + 'Z',
            'end': now.isoformat() + 'Z'
        }
    }
    
    # Add additional filters if provided
    if filters:
        query['filter'].extend(filters)

    response = requests.post(
        f'https://api.honeycomb.io/1/queries/{dataset}',
        headers=headers,
        json=query
    )
    
    if response.status_code != 200:
        raise Exception(f"Honeycomb API error: {response.text}")
        
    return response.json()

result = analyze_traces(api_key, dataset, service_name, start_time, filters)
print(json.dumps(result, indent=2))
    """,
    args=[
        Arg(name="api_key", type="str", description="Honeycomb API key", required=True),
        Arg(name="dataset", type="str", description="Honeycomb dataset", required=True),
        Arg(name="service_name", type="str", description="Service name to analyze", required=True),
        Arg(name="start_time", type="int", description="Start time in minutes ago", required=True),
        Arg(name="filters", type="list", description="Additional filters to apply", required=False),
    ],
)

tool_registry.register("honeycomb", analyze_traces) 


