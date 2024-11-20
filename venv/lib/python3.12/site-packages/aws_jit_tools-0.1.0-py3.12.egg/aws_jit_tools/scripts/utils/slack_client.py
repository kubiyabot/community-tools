import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SlackClient:
    def __init__(self):
        self.token = os.environ.get('SLACK_API_TOKEN')
        self.channel_id = os.environ.get('SLACK_CHANNEL_ID')
        self.thread_ts = os.environ.get('SLACK_THREAD_TS') # Optional
        
        if not self.token or not self.channel_id:
            logger.warning("SLACK_API_TOKEN or SLACK_CHANNEL_ID not set")

    def send_message(self, message: str = None, blocks: Dict[str, Any] = None) -> bool:
        """Send a Slack message with optional blocks."""
        if not self.token or not self.channel_id:
            logger.error("Slack credentials not properly configured - please make sure you have enabled Slack integration on the execution environment (team mate)")
            return False

        try:
            payload = {'channel': self.channel_id}
            
            if self.thread_ts:
                payload['thread_ts'] = self.thread_ts
            if blocks:
                payload['blocks'] = blocks.get('blocks', [])
            if message:
                payload['text'] = message

            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers={'Authorization': f'Bearer {self.token}'},
                json=payload
            )

            if not response.ok:
                logger.error(f"Failed to send Slack message: {response.text}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False

    def lookup_user_by_email(self, email: str) -> Optional[str]:
        """Look up Slack user ID by email."""
        if not self.token:
            logger.error("SLACK_API_TOKEN not set")
            return None

        try:
            response = requests.post(
                'https://slack.com/api/users.lookupByEmail',
                headers={'Authorization': f'Bearer {self.token}'},
                data={'email': email}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data['user']['id']
            
            logger.error(f"Failed to find Slack user for email: {email}")
            return None

        except Exception as e:
            logger.error(f"Error looking up Slack user: {str(e)}")
            return None 