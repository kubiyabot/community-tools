import os
import sqlite3
from datetime import datetime, timedelta, timezone
import requests
import sys
from pytimeparse.timeparse import timeparse

DELETION_ENABLED = os.getenv("RESOURCE_DELETION_ENABLED", "false").lower() == "true"

def parse_duration(duration):
    seconds = timeparse(duration)
    if seconds is None:
        print("Error: Invalid duration format. Please use a valid format (e.g., 5h for 5 hours, 30m for 30 minutes).")
        sys.exit(1)
    return timedelta(seconds=seconds)

def calculate_schedule_time(duration):
    now = datetime.now(timezone.utc)  # Get the current time in UTC with timezone
    return now + parse_duration(duration)

def schedule_deletion(request_id, duration):
    if not DELETION_ENABLED:
        print("Resource deletion is not enabled. Please ask the oprator who created this task to set the RESOURCE_DELETION_ENABLED environment variable to 'true' to enable it.")
    ttl_seconds = timeparse(duration)
    initial_schedule_time = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS follow_ups (request_id text, action text, schedule_time text)''')
    c.execute("INSERT INTO follow_ups VALUES (?, ?, ?)", (request_id, 'nag', initial_schedule_time))
    conn.commit()
    conn.close()

    print(f"Scheduled initial nagging for request {request_id} at {initial_schedule_time}")

def main(schedule_time):
    required_vars = [
        "KUBIYA_API_KEY", "SLACK_CHANNEL_ID", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_PROFILE"
    ]
    for var in required_vars:
        if var not in os.environ:
            print(f"Error: {var} is not set. Please set the {var} environment variable.")
            sys.exit(1)

    payload = {
        "schedule_time": schedule_time,
        "channel_id": os.environ["SLACK_CHANNEL_ID"],
        "user_email": os.environ["KUBIYA_USER_EMAIL"],
        "organization_name": os.environ["KUBIYA_USER_ORG"],
        "task_description": "Follow-up reminder",
        "agent": os.environ["KUBIYA_AGENT_PROFILE"]
    }
    response = requests.post(
        'https://api.kubiya.ai/api/v1/scheduled_tasks',
        headers={
            'Authorization': f'UserKey {os.environ["KUBIYA_API_KEY"]}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    if response.status_code < 300:
        print(f"Task scheduled successfully. Response: {response.text}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Schedule resource deletion with nagging mechanism.')
    parser.add_argument('request_id', type=str, help='The request ID')
    parser.add_argument('duration', type=str, help='Duration before initial nagging (e.g., 3h, 1d, 1m)')

    args = parser.parse_args()
    schedule_deletion(args.request_id, args.duration)
    duration = args.duration
    schedule_time = calculate_schedule_time(duration)
    print(f"Scheduling task for {schedule_time}")
    main(schedule_time.isoformat())  # Use isoformat to include timezone info
