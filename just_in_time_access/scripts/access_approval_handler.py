import sys
import os
import sqlite3
import requests
import json
from datetime import datetime

def approve_access(request_id, approval_action, ttl=None):
    slack_token = os.getenv('SLACK_API_TOKEN')
    approver_email = os.getenv('KUBIYA_USER_EMAIL')

    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    # Fetch the request details from the database
    cursor.execute('''
        SELECT tool_name, user_email, tool_params, ttl
        FROM requests WHERE request_id=?
    ''', (request_id,))
    row = cursor.fetchone()
    if row is None:
        print(f"Request ID {request_id} not found in the database.")
        sys.exit(1)

    tool_name, requester_email, tool_params, original_ttl = row

    if approval_action.lower() == 'approve':
        if ttl is None:
            # If TTL is not provided by the approver, use the TTL from the original request
            ttl = original_ttl

        # Notify requester in Slack
        notify_user(request_id, "approved", requester_email, approver_email)

        # Send HTTP request to the auth server
        auth_server_url = os.getenv('KUBIYA_ENFORCER_SERVER_URL', 'http://enforcer.kubiya:5001')
        api_endpoint = f"{auth_server_url}/policies"

        # Prepare the payload for the auth server
        payload = {
            "ttl": ttl,
            "policy": {
                "user": {
                    "email": requester_email,
                    "groups": []
                },
                "tool": {
                    "source_url": os.getenv('KUBIYA_SOURCE_URL'),
                    "name": tool_name,
                    "parameters": json.loads(tool_params)
                },
                "source": {
                    "url": os.getenv('KUBIYA_SOURCE_URL'),
                    "id": os.getenv('KUBIYA_SOURCE_UUID')
                }
            }
        }

        # Send POST request to the auth server
        response = requests.post(api_endpoint, json=payload)
        if response.status_code != 200:
            print(f"Failed to send approval to auth server: {response.text}")
            sys.exit(1)
        else:
            print("Approval notification sent to auth server successfully.")

        # Update the TTL and status in the database
        cursor.execute('''
            UPDATE requests SET ttl=?, status='approved' WHERE request_id=?
        ''', (ttl, request_id))
        conn.commit()

    elif approval_action.lower() == 'reject':
        # Notify requester in Slack
        notify_user(request_id, "rejected", requester_email, approver_email)

        # Update status in the database
        cursor.execute('''
            UPDATE requests SET status='rejected' WHERE request_id=?
        ''', (request_id,))
        conn.commit()
    else:
        print("Invalid approval action. Use 'approve' or 'reject'.")
        sys.exit(1)

    conn.close()

def notify_user(request_id, status, user_email, approver_email):
    slack_token = os.getenv('SLACK_API_TOKEN')

    # Translate email to Slack user ID
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {slack_token}'
    }
    params = {
        'email': user_email
    }
    user_info_response = requests.get('https://slack.com/api/users.lookupByEmail', headers=headers, params=params)

    if user_info_response.status_code != 200 or not user_info_response.json().get('ok'):
        print(f"Failed to retrieve user ID: {user_info_response.text}")
        sys.exit(1)

    user_id = user_info_response.json()['user']['id']

    # Prepare the Block Kit message
    approval_status = "approved" if status == "approved" else "rejected"
    message = {
        "channel": user_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: Your access request *{request_id}* has been *{approval_status.upper()}* by {approver_email}."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Request Details:*\n- *Request ID:* {request_id}\n- *Status:* {approval_status.capitalize()}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"If you have questions, reach out to *{approver_email}*."
                    }
                ]
            }
        ]
    }

    # Send the message to Slack
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}'
    }
    response = requests.post('https://slack.com/api/chat.postMessage', headers=headers, data=json.dumps(message))

    if response.status_code != 200 or not response.json().get('ok'):
        print(f"Failed to send notification: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: access_approval_handler.py <request_id> <approve/reject> [ttl]")
        sys.exit(1)

    request_id = sys.argv[1]
    approval_action = sys.argv[2]
    ttl = sys.argv[3] if len(sys.argv) > 3 else None

    approve_access(request_id, approval_action, ttl)
