import sys
import os
import json
import requests
from datetime import datetime, timedelta

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
    
    # Check if the request was successful
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Request failed: {str(e)}",
            "status_code": response.status_code,
            "response_text": response.text
        }

    # Try to parse JSON response
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        return {
            "error": f"Failed to parse JSON response: {str(e)}",
            "response_text": response.text
        }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Honeycomb traces")
    parser.add_argument("dataset", help="Honeycomb dataset name")
    parser.add_argument("service_name", help="Service name to analyze")
    parser.add_argument("start_time", type=int, help="Minutes to look back")
    
    args = parser.parse_args()

    # Validate required arguments
    if not all([args.dataset, args.service_name, args.start_time]):
        print(json.dumps({"error": "Missing required arguments: dataset, service_name, or start_time"}))
        sys.exit(1)

    # Validate Honeycomb connection
    error = validate_honeycomb_connection()
    if error:
        print(error)
        sys.exit(1)

    # Calculate time range
    start_time_str, end_time_str = calculate_time_range(args.start_time)

    # Build Honeycomb query
    query = {
        "calculations": [
            {"op": "P99", "column": "duration_ms"},
            {"op": "COUNT"},
            {"op": "AVG", "column": "duration_ms"}
        ],
        "filter": [
            {"column": "service_name", "op": "equals", "value": args.service_name}
        ],
        "time_range": {
            "start": start_time_str,
            "end": end_time_str
        }
    }

    # Send request to Honeycomb
    response = make_honeycomb_request(
        f"https://api.honeycomb.io/1/query/{args.dataset}",
        query
    )

    # Output response
    print(json.dumps(response))

if __name__ == "__main__":
    main() 