import requests
import os

class SlackMessage:
    def __init__(self, channel, thread_ts=None):
        self.channel = channel or os.getenv('SLACK_CHANNEL_ID')
        self.thread_ts = os.getenv('SLACK_THREAD_TS') or thread_ts
        self.blocks = []
        self.api_key = os.getenv('SLACK_API_TOKEN')
        self.message_ts = None  # To store the timestamp of the message

    def send_initial_message(self, blocks):
        self.blocks = blocks
        response = self.send_message()
        if response and 'ts' in response:
            self.message_ts = response['ts']
        else:
            print(f"Failed to send message. Response: {response}")

    def update_message(self):
        self.send_message(update=True)

    def send_message(self, update=False):
        if not self.api_key:
            if os.getenv('KUBIYA_DEBUG'):
                print("No SLACK_API_TOKEN set. Slack messages will not be sent.")
            return None

        payload = {
            "channel": self.channel,
            "blocks": self.blocks
        }
        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts

        url = "https://slack.com/api/chat.postMessage"
        if update and self.message_ts:
            payload["ts"] = self.message_ts
            url = "https://slack.com/api/chat.update"

        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            },
            json=payload
        )
        if response.status_code >= 300:
            if os.getenv('KUBIYA_DEBUG'):
                print(f"Error sending Slack message: {response.status_code} - {response.text}")
            return None
        else:
            return response.json()
