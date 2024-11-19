import os
import sqlite3
from datetime import datetime, timedelta
from pytimeparse.timeparse import timeparse

def extend_resource_ttl(request_id, extension_period):
    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute("SELECT expiry_time FROM resources WHERE request_id=?", (request_id,))
    resources = c.fetchall()

    if resources:
        for resource in resources:
            current_expiry_time = datetime.fromisoformat(resource[0])
            new_expiry_time = (current_expiry_time + timedelta(seconds=extension_period)).isoformat()
            c.execute("UPDATE resources SET expiry_time=? WHERE request_id=?", (new_expiry_time, request_id))
        conn.commit()
        print(f"Extended TTL for resources under request ID {request_id} by {extension_period} seconds")
    else:
        print(f"No resources found for request ID {request_id}")
    
    conn.close()

def handle_slack_response(request_id, user_response):
    if user_response.lower() == 'extend':
        EXTENSION_PERIOD = timeparse(os.getenv('EXTENSION_PERIOD', '1w'))
        extend_resource_ttl(request_id, EXTENSION_PERIOD)
    else:
        print(f"Received unrecognized response: {user_response}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Handle user response to TTL extension reminder.')
    parser.add_argument('request_id', type=str, help='The request ID')
    parser.add_argument('response', type=str, help='User response (e.g., "extend" to extend TTL)')

    args = parser.parse_args()
    handle_slack_response(args.request_id, args.response)
