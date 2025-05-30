import sys
import os
import json
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    # During discovery phase, requests might not be available
    pass

def send_k8s_alert(channel, alert_title, alert_message, proposed_action):
    """
    Send a Kubernetes alert notification to a Slack channel with an approval button
    """
    slack_token = os.environ["SLACK_API_TOKEN"]

    # Prepare the Block Kit message
    message = {
        "channel": channel,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":warning: {alert_title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Kubernetes Alert Detected*\n{alert_message}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":robot_face: *Proposed Action:*\n{proposed_action}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":white_check_mark: *Ready to approve this action?*\nClick the button below to authorize the AI to proceed!"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve Action",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": json.dumps({
                            "agent_uuid": os.environ.get("KUBIYA_AGENT_UUID", ""),
                            "message": f"AUTONOMOUS EXECUTION REQUIRED: Use the kubectl tool to {proposed_action}. You must complete this action fully and autonomously without asking for any user input, confirmation, or additional information. If you encounter any issues or need additional steps, resolve them automatically using your best judgment. Do not ask questions - take action immediately and complete the task."
                        }),
                        "action_id": "agent.process_message_1"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Deny",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": json.dumps({
                            "agent_uuid": os.environ.get("KUBIYA_AGENT_UUID", ""),
                            "message": "Deny the proposed action"
                        }),
                        "action_id": "agent.process_message_2"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
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
        print(f"Failed to send alert: {response.text}")
        sys.exit(1)
    
    print(f"Successfully sent Kubernetes alert to channel {channel}")

if __name__ == "__main__":
    # Read arguments from environment variables
    try:
        channel = os.environ["ALERT_CHANNEL"]
        alert_title = os.environ["ALERT_TITLE"]
        alert_message = os.environ["ALERT_MESSAGE"]
        proposed_action = os.environ["PROPOSED_ACTION"]
    except KeyError as e:
        print(f"Missing required environment variable: {e}")
        sys.exit(1)
    
    send_k8s_alert(channel, alert_title, alert_message, proposed_action)