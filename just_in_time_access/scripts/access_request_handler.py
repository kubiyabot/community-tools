import sys
import os
import json
import requests
import sqlite3
import uuid

def send_approval_request(tool_name, user_email, tool_params, ttl):
    approval_channel = os.getenv('APPROVALS_CHANNEL_ID')
    slack_token = os.getenv('SLACK_API_TOKEN')
    database_path = '/var/lib/database/access_requests.db'

    request_id = str(uuid.uuid4())

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            user_email TEXT,
            tool_name TEXT,
            tool_params TEXT,
            ttl TEXT,
            status TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO requests (request_id, user_email, tool_name, tool_params, ttl, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_email, tool_name, tool_params, ttl, 'pending'))

    conn.commit()
    conn.close()

    approval_message = {
        "channel": approval_channel,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Access Request*\n\n*Request ID:* `{request_id}`\n*User:* `{user_email}`\n*Tool:* `{tool_name}`\n*Parameters:* `{tool_params}`\n*TTL:* `{ttl}`"
                }
            },
            {
                "type": "actions",
                "block_id": request_id,
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Approve"
                        },
                        "style": "primary",
                        "value": "approve"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Reject"
                        },
                        "style": "danger",
                        "value": "reject"
                    }
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}'
    }
    response = requests.post('https://slack.com/api/chat.postMessage', headers=headers, data=json.dumps(approval_message))

    if response.status_code != 200 or not response.json().get('ok'):
        print(f"Failed to send approval request: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    tool_name = sys.argv[1]
    user_email = sys.argv[2]
    tool_params = sys.argv[3]
    ttl = sys.argv[4] if len(sys.argv) > 4 else "1h"

    send_approval_request(tool_name, user_email, tool_params, ttl) 