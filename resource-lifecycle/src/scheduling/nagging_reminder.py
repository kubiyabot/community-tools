import os
import sqlite3
from datetime import datetime, timedelta
import requests
from pytimeparse.timeparse import timeparse

def send_slack_reminder(request_id, user_email, resource_details, expiry_time):
    slack_channel_id = os.getenv('APPROVAL_SLACK_CHANNEL')
    slack_token = os.getenv('SLACK_API_TOKEN')

    reminder_message = f"Reminder: The resources under request ID {request_id} are set to expire at {expiry_time}. Please respond with 'extend' to extend the TTL."

    payload = {
        "channel": slack_channel_id,
        "text": reminder_message
    }

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {slack_token}'
        },
        json=payload
    )

    if response.status_code < 300:
        print(f"Slack reminder sent successfully for request ID {request_id}")
    else:
        print(f"Error sending Slack reminder: {response.status_code} - {response.text}")

def handle_nagging():
    GRACE_PERIOD = timeparse(os.getenv('GRACE_PERIOD', '5h'))

    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()
    now = datetime.utcnow().isoformat()

    c.execute("SELECT request_id, user_email, resource_details, expiry_time FROM resources WHERE expiry_time <= ?", (now,))
    expiring_resources = c.fetchall()

    for resource in expiring_resources:
        request_id, user_email, resource_details, expiry_time = resource
        send_slack_reminder(request_id, user_email, resource_details, expiry_time)

        next_schedule_time = (datetime.utcnow() + timedelta(seconds=GRACE_PERIOD)).isoformat()
        c.execute("UPDATE resources SET expiry_time=? WHERE request_id=?", (next_schedule_time, request_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    handle_nagging()
