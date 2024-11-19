import os
import sqlite3
import sys
import json
from datetime import datetime, timedelta
from pytimeparse.timeparse import timeparse
from iac.terraform import apply_terraform
from litellm import completion
import requests
import subprocess
from slack.slack import SlackMessage
from approval.scheduler import schedule_deletion_task

def get_access_instructions(resource_details):
    sys_prompt = f"""
    Given the following resource details, please provide instructions on how to access and use the resources created:
    {json.dumps(resource_details, indent=2)}
    """
    messages = [{"content": sys_prompt, "role": "system"}]
    response = completion(
        model="gpt-4o",
        messages=messages,
        format="json"
    )
    instructions = response['choices'][0]['message']['content']
    return instructions

def approve_request(request_id, approval_action, user_email):
    APPROVING_USERS = os.getenv('APPROVING_USERS', '').split(',')
    APPROVAL_SLACK_CHANNEL = os.getenv('APPROVAL_SLACK_CHANNEL')

    slack_msg = SlackMessage(APPROVAL_SLACK_CHANNEL)

    if user_email not in APPROVING_USERS:
        slack_msg.update_message(f"❌ User {user_email} is not authorized to approve this request.")
        print(f"User {user_email} is not authorized to approve this request")
        sys.exit(1)

    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute("SELECT * FROM approvals WHERE request_id=? AND approved='pending'", (request_id,))
    approval_request = c.fetchone()

    if not approval_request:
        slack_msg.update_message(f"❌ No pending approval request found for request ID {request_id}")
        print(f"No pending approval request found for request ID {request_id}")
        sys.exit(1)

    c.execute("UPDATE approvals SET approved=? WHERE request_id=?", (approval_action, request_id))
    conn.commit()

    if approval_action == 'approved':
        c.execute("SELECT * FROM tf_plans WHERE request_id=?", (request_id,))
        tf_plan_data = c.fetchone()

        if not tf_plan_data:
            slack_msg.update_message(f"❌ No Terraform plan found for request ID {request_id}")
            print(f"No Terraform plan found for request ID {request_id}")
            sys.exit(1)

        tf_plan = tf_plan_data[1]
        cost_data = json.loads(tf_plan_data[2])

        c.execute("SELECT * FROM resources WHERE request_id=?", (request_id,))
        resource_request = c.fetchone()

        if not resource_request:
            slack_msg.update_message(f"❌ No resource request found for request ID {request_id}")
            print(f"No resource request found for request ID {request_id}")
            sys.exit(1)

        resource_details = json.loads(resource_request[1])
        tf_files = json.loads(resource_request[2])

        try:
            apply_output, tf_state = apply_terraform(tf_files, request_id)
            access_instructions = get_access_instructions(resource_details)
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Resources for request ID {request_id} have been created successfully*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{apply_output}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Access Instructions:*\n{access_instructions}"
                    }
                }
            ]
            slack_msg.send_block_message(blocks)

            # Store the state in the database
            c.execute("UPDATE resources SET tf_state=? WHERE request_id=?", (tf_state, request_id))
            conn.commit()

        except subprocess.CalledProcessError:
            slack_msg.update_message(f"❌ Error applying resources for request ID {request_id}!\n\n```{apply_output}```")
            print(f"Error applying resources for request ID {request_id}: ```{apply_output}```")
            sys.exit(1)

        ttl = timeparse(approval_request[7])
        schedule_deletion_task(request_id, ttl, approval_request[10])

    slack_msg.update_message(f"✅ Approval request with ID {request_id} has been {approval_action} by {user_email}")

    action_emoji = ":white_check_mark:" if approval_action == "approved" else ":x:"
    action_text = "approved" if approval_action == "approved" else "rejected"
    approver_text = f"<@{user_email}> {action_text} this request {action_emoji}"

    slack_channel_id = approval_request[8]
    slack_thread_ts = approval_request[9]

    # Get permalink
    permalink_response = requests.get(
        "https://slack.com/api/chat.getPermalink",
        params={
            'channel': slack_channel_id,
            'message_ts': slack_thread_ts
        },
        headers={
            'Authorization': f'Bearer {os.getenv("SLACK_API_TOKEN")}'
        }
    )
    permalink = permalink_response.json().get("permalink")

    slack_payload_main_thread = {
        "channel": slack_channel_id,
        "text": f"<@{approval_request[1]}>, your request has been {approval_action}.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Request {approval_action}* {action_emoji}\n*Reason:* {approval_request[2]}\n*Status:* {approver_text}\n<{permalink}|View original conversation>"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "↗️💬 View Thread"
                        },
                        "url": permalink
                    }
                ]
            }
        ],
    }

    slack_payload_in_thread = {
        "channel": slack_channel_id,
        "text": f"<@{approval_request[1]}>, your request has been {approval_action}.",
        "thread_ts": slack_thread_ts,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your resources have been created successfully!*\n{approver_text} :tada:\n\nHere are the details and access instructions:\n{access_instructions}"
                }
            }
        ]
    }

    for slack_payload in [slack_payload_main_thread, slack_payload_in_thread]:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("SLACK_API_TOKEN")}'
            },
            json=slack_payload
        )

        if response.status_code >= 300:
            if os.getenv('KUBIYA_DEBUG'):
                print(f"Error sending Slack message: {response.status_code} - {response.text}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Approve or reject a resource creation request.')
    parser.add_argument('request_id', type=str, help='The unique identifier for the request being approved or rejected')
    parser.add_argument('approval_action', type=str, choices=['approved', 'rejected'], help='Approval action (approved or rejected)')

    args = parser.parse_args()
    approve_request(args.request_id, args.approval_action, os.getenv('KUBIYA_USER_EMAIL'))
