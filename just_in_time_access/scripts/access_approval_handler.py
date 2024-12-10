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


def get_request_metadata(request_id: str, enforcer_base_url: str) -> dict:
    response = requests.get(f"{enforcer_base_url}/requests/describe/{request_id}")
    if response.status_code >= 400:
        print(f"Failed to fetch request details: {response.text}")
        sys.exit(1)

    return response.json()


from datetime import datetime, timedelta, timezone


# Function to convert 'xh' format to a future date
def convert_to_future_date(duration: str) -> datetime:
    # Get current time
    current_time = datetime.now(timezone.utc)

    unit = duration[-1:]  # Extract the unit of time from the string
    duration_format = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
    }
    d = duration_format.get(unit, None)
    if d is None:
        raise ValueError(
            "Invalid duration format. Please use a valid format (e.g., 5h for 5 hours, 30m for 30 minutes). Seconds, Minutes, Hours, Days are supported."
        )
    # Extract the number of hours from the string
    value = int(duration[:-1])  # Remove the 'h' and convert the number to int
    # Add the number of hours to the current time
    future_time = current_time + timedelta(**{d: value})

    return future_time


def schedule_task(
    teammate: str,
    schedule_time: datetime,
    slack_destination: str,
    ai_instructions: str,
):
    schedule_time_str = schedule_time.isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )
    payload = {
        "channel_id": slack_destination,
        "cron_string": None,
        "schedule_time": schedule_time_str,
        "selected_agent": teammate,
        "task_description": ai_instructions,
    }

    max_retries = 3
    for attempt in range(max_retries):
        response = requests.post(
            "https://api.kubiya.ai/api/v1/scheduled_tasks",
            headers={
                "Authorization": f'UserKey {os.environ["KUBIYA_API_KEY"]}',
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code < 400:
            break
        else:
            print(f"Attempt {attempt + 1} failed: {response.text}")
            if attempt < max_retries - 1:
                print("Retrying...")
            else:
                print("Max retries reached. Unable to schedule task.")
                sys.exit(1)

    print("Task scheduled successfully.")


def approve(request_id: str, ttl: str, approve_email: str, enforcer_base_url: str):
    print(f"🚀 Approving request {request_id} with TTL {ttl}.")
    request_metadata = get_request_metadata(request_id, enforcer_base_url)

    end_datetime = convert_to_future_date(ttl)
    metadata_str = ""
    for key, value in request_metadata.items():
        metadata_str += f"{key}: {value}\n"
    schedule_task(
        teammate=os.environ["KUBIYA_AGENT_NAME"],
        schedule_time=end_datetime,
        slack_destination=os.environ["SLACK_CHANNEL_ID"],
        ai_instructions=f"Your task is to revoke the access granted based on the following approved request details:\n{metadata_str}\n\n If a suitable tool or method is available to revoke the permissions, please execute the action immediately with the relevant context",
    )
    print("📅 Revoke task scheduled successfully.")

    response = requests.put(
        f"{enforcer_base_url}/requests/approve",
        json={"id": request_id, "ttl": ttl, "user_email": approve_email},
    )
    if response.status_code != 200:
        print(f"Failed to approve request: {response.text}")
        sys.exit(1)

    print("🎉 Request approved successfully.")


def approve_access(request_id: str, approval_action: str, ttl: str | None = None):
    approver_email = os.environ["KUBIYA_USER_EMAIL"]

    enforcer_base_url = "http://enforcer.kubiya:5001"
    requester_email = get_requester_email(request_id, enforcer_base_url)
    if approval_action.lower() == "approve":
        if ttl is None:
            print("Please provide a TTL for the approved request.")
            sys.exit(1)

        approve(request_id, ttl, approver_email, enforcer_base_url)

        # Notify requester in Slack
        notify_user(request_id, "approved", requester_email, approver_email)

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
    enforcer_base_url = "http://enforcer.kubiya:5001"

    # Get request details to include tool info
    request_data = get_request_metadata(request_id, enforcer_base_url)
    tool_name = request_data["request"]["tool"]["name"]
    tool_params = request_data["request"]["tool"]["parameters"]

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
    emoji = ":white_check_mark:" if status == "approved" else ":x:"
    
    message = {
        "channel": user_id,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Access Request {approval_status.capitalize()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi <@{user_id}> :wave:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your access request has been *{approval_status}* by {approver_email}."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*🔑 Tool:*\n" + tool_name
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*📝 Request ID:*\n" + request_id
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*⚙️ Parameters:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{json.dumps(tool_params, indent=2)}```"
                }
            }
        ]
    }

    # Add status-specific content
    if status == "approved":
        message["blocks"].extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":rocket: *Ready to use your new access?*\nClick the button below to execute the approved tool right away!"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Use your new access",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": json.dumps({
                            "agent_uuid": os.environ.get("KUBIYA_AGENT_UUID", ""),
                            "message": f"I just got approved to perform tool {tool_name} with params {json.dumps(tool_params)} - execute it right away"
                        }),
                        "action_id": "agent.process_message_1"
                    }
                ]
            }
        ])
    else:
        message["blocks"].extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":information_source: If you believe this rejection was a mistake or need to discuss further, please reach out to the approver."
                }
            }
        ])

    # Add footer with additional information
    message["blocks"].extend([
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"👤 Approved by: {approver_email}"
                }
            ]
        }
    ])

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
