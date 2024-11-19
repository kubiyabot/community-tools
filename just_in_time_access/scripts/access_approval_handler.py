import sys
import os
import json

try:
    import requests
except ImportError:
    # During discovery phase, requests might not be available
    pass


def get_requester_email(request_id: str, enforcer_base_url: str) -> str:
    response = requests.get(f"{enforcer_base_url}/requests/describe/{request_id}")
    if response.status_code != 200:
        print(f"Failed to fetch request details: {response.text}")
        sys.exit(1)

    request_details = response.json()
    return request_details["request"]["user"]["email"]


def approve(request_id: str, ttl: str, enforcer_base_url: str):
    response = requests.put(
        f"{enforcer_base_url}/requests/approve",
        json={"id": request_id, "ttl": ttl},
    )
    if response.status_code != 200:
        print(f"Failed to approve request: {response.text}")
        sys.exit(1)


def approve_access(request_id: str, approval_action: str, ttl: str | None = None):
    approver_email = os.environ["KUBIYA_USER_EMAIL"]

    enforcer_base_url = "http://enforcer.kubiya:5001"
    requester_email = get_requester_email(request_id, enforcer_base_url)
    if approval_action.lower() == "approve":
        if ttl is None:
            print("Please provide a TTL for the approved request.")
            sys.exit(1)
        # Notify requester in Slack
        notify_user(request_id, "approved", requester_email, approver_email)

        approve(request_id, ttl, enforcer_base_url)

        print("Access request approved successfully.")

    elif approval_action.lower() == "reject":
        # Notify requester in Slack
        notify_user(request_id, "rejected", requester_email, approver_email)
        print("Access request rejected successfully.")

    else:
        print("Invalid approval action. Use 'approve' or 'reject'.")
        sys.exit(1)


def notify_user(request_id, status, user_email, approver_email):
    slack_token = os.environ["SLACK_API_TOKEN"]

    # Translate email to Slack user ID
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {slack_token}",
    }
    params = {"email": user_email}
    user_info_response = requests.get(
        "https://slack.com/api/users.lookupByEmail", headers=headers, params=params
    )

    if user_info_response.status_code != 200 or not user_info_response.json().get("ok"):
        print(f"Failed to retrieve user ID: {user_info_response.text}")
        sys.exit(1)

    user_id = user_info_response.json()["user"]["id"]

    # Prepare the Block Kit message
    approval_status = "approved" if status == "approved" else "rejected"
    message = {
        "channel": user_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: Your access request *{request_id}* has been *{approval_status.upper()}* by {approver_email}.",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Request Details:*\n- *Request ID:* {request_id}\n- *Status:* {approval_status.capitalize()}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"If you have questions, reach out to *{approver_email}*.",
                    }
                ],
            },
        ],
    }

    # Send the message to Slack
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {slack_token}",
    }
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        data=json.dumps(message),
    )

    if response.status_code != 200 or not response.json().get("ok"):
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
