import os
import sqlite3
import subprocess
import json
import sys
from iac.terraform import destroy_terraform
import subprocess
from slack.slack import SlackMessage

def destroy_resources(request_id: str):
    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute("SELECT * FROM resources WHERE request_id=?", (request_id,))
    resource_request = c.fetchone()

    if not resource_request:
        print(f"❌ No resource request found for request ID {request_id}")
        return False, "No resource request found"

    tf_files = json.loads(resource_request[1])

    try:
        destroy_output = destroy_terraform(tf_files, request_id)
        return True, destroy_output
    except subprocess.CalledProcessError as e:
        log_message = f"Error in destroying resources: ```{destroy_output}```"
        print(log_message)
        return False, str(e)

def notify_user_and_approver(request_id, destroy_output):
    conn = sqlite3.connect('/sqlite_data/approval_requests.db')
    c = conn.cursor()

    c.execute("SELECT * FROM approvals WHERE request_id=?", (request_id,))
    approval_request = c.fetchone()

    if not approval_request:
        print(f"❌ No approval request found for request ID {request_id}")
        return

    user_email = approval_request[1]

    slack_channel_id = approval_request[9]
    slack_thread_ts = approval_request[10]

    slack_msg = SlackMessage(slack_channel_id, slack_thread_ts)

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🗑️ *Resources for request ID {request_id} have been deleted as the TTL has expired*\n\nOriginally requested by: {user_email}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{destroy_output}```"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*If you need an extension, please reply in the thread to request approval from an admin*\n\n* You will need to provide a reason for the extension request"
            }
        }
    ]

    slack_msg.send_block_message(blocks)

    # Also send in the approvers channel
    approvers_channel_id = os.getenv('APPROVING_SLACK_CHANNEL')
    slack_msg = SlackMessage(approvers_channel_id)
    slack_msg.send_block_message(blocks)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Destroy resources created by Terraform.')
    parser.add_argument('request_id', type=str, help='The unique identifier for the resource to be destroyed')

    user_email = os.getenv('KUBIYA_USER_EMAIL')
    approving_users = os.getenv('APPROVING_USERS').split(',')
    if user_email not in approving_users:
        print(f"❌ User {user_email} is not authorized to destroy resources")
        sys.exit(1)

    args = parser.parse_args()
    success, output = destroy_resources(args.request_id)
    if success:
        print(f"✅ Resources destroyed successfully:\n{output}")
        notify_user_and_approver(args.request_id, output)
    else:
        print(f"❌ Failed to destroy resources:\n{output}")
