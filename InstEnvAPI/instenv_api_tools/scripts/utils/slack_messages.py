import os
import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

class SlackMessage:
    def __init__(self, channel: str = None):
        """Initialize Slack message handler."""
        self.channel = channel or os.getenv('SLACK_CHANNEL_ID')
        self.api_token = os.getenv('SLACK_API_TOKEN')
        self.thread_ts = os.getenv('SLACK_THREAD_TS')

    def send_message(self, blocks: List[Dict]) -> bool:
        """Send a Slack message with blocks."""
        if not self.api_token:
            logger.warning("No SLACK_API_TOKEN set. Slack messages will not be sent.")
            return False

        try:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_token}'
                },
                json={
                    "channel": self.channel,
                    "thread_ts": self.thread_ts,
                    "blocks": blocks
                }
            )
            
            if response.status_code >= 300:
                logger.error(f"Error sending Slack message: {response.status_code} - {response.text}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    def send_analysis_results(self, analysis_results: List[Dict]) -> bool:
        """Send analysis results to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔍 Environment Failure Analysis",
                    "emoji": True
                }
            }
        ]

        for result in analysis_results:
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{result.reason}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*How to Fix:*\n{result.how_to_fix}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Suggested Changes:*\n{result.suggested_payload_changes}"
                    }
                },
                {"type": "divider"}
            ])

        return self.send_message(blocks) 