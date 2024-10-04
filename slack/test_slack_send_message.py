import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def test_slack_send_message():
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        print("Error: SLACK_API_TOKEN is not set.")
        return

    client = WebClient(token=token)
    channel = "#general"  # Replace with a channel where your app is invited
    message = "Hello, this is a test message from the Kubiya Slack integration!"

    try:
        print(f"Attempting to send message to channel: {channel}")
        response = client.chat_postMessage(channel=channel, text=message)
        print(f"Message sent successfully. Response: {response}")
        print(f"Message timestamp: {response['ts']}")
        print(f"Channel: {response['channel']}")
        print(f"Message text: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e}")
        print(f"Error details: {e.response['error']}")
        print(f"Full response: {e.response}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_slack_send_message()