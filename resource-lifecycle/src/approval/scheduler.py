import os
import sys
from datetime import datetime, timedelta
import requests
from slack.slack import SlackMessage

def parse_duration(duration):
    try:
        seconds = int(duration)
        return timedelta(seconds=seconds)
    except ValueError:
        print("Error: Invalid duration format. Please provide the TTL as an integer representing seconds.")
        sys.exit(1)

def calculate_schedule_time(duration):
    now = datetime.utcnow()
    return now + parse_duration(duration)

def schedule_deletion_task(request_id, ttl, slack_thread_ts):
    if not os.getenv("RESOURCE_DELETION_ENABLED", "false").lower() == "true":
        print("Resource deletion is not enabled. Please ask the operator who created this task to set the RESOURCE_DELETION_ENABLED environment variable to 'true' to enable it.")
        return
    schedule_time = calculate_schedule_time(ttl).isoformat()

    task_payload = {
        "schedule_time": schedule_time,
        "task_description": f"Delete resources associated with request ID {request_id} as the TTL has expired.",
        "channel_id": os.getenv("NOTIFICATION_CHANNEL_ID") or os.getenv("APPROVAL_SLACK_CHANNEL") or os.getenv("SLACK_CHANNEL_ID"),
        "user_email": os.getenv("KUBIYA_USER_EMAIL"), # the user who is responsible for the resources being deleted (task will get reported to him)
        "organization_name": os.getenv("KUBIYA_USER_ORG"),
        "agent": os.getenv("KUBIYA_AGENT_PROFILE"),
        "thread_ts": slack_thread_ts,
        "request_id": request_id
    }

    response = requests.post(
        'https://api.kubiya.ai/api/v1/scheduled_tasks',
        headers={
            'Authorization': f'UserKey {os.getenv("KUBIYA_API_KEY")}',
            'Content-Type': 'application/json'
        },
        json=task_payload
    )

    if response.status_code >= 300:
        slack_msg = SlackMessage(os.getenv('SLACK_CHANNEL_ID'), slack_thread_ts)
        slack_msg.update_message(f"❌ Error scheduling task for request ID {request_id}: {response.status_code} - {response.text}")
        print(f"Error scheduling task: {response.status_code} - {response.text}")
        sys.exit(1)
    else:
        print(f"Task scheduled successfully for request ID {request_id}.")

if __name__ == "__main__":
    required_vars = [
        "KUBIYA_API_KEY", "SLACK_CHANNEL_ID", "KUBIYA_USER_ORG", "KUBIYA_AGENT_PROFILE"
    ]
    for var in required_vars:
        if var not in os.environ:
            print(f"Error: {var} is not set. Please set the {var} environment variable.")
            sys.exit(1)
