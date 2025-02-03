import os
import json
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class KubiyaChatClient:
    def __init__(self):
        self.base_url = os.environ.get('KUBIYA_API_URL', 'https://api.kubiya.ai')
        self.api_key = os.environ.get('KUBIYA_API_KEY')
        if not self.api_key:
            raise ValueError("KUBIYA_API_KEY environment variable is required")

    def send_message(self, message: str, teammate_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to a teammate and get their response."""
        if not teammate_id:
            teammate_id = os.environ.get('GIT_TEAMMATE_NAME', 'ci_cd_guardians')

        headers = {
            'Authorization': f'UserKey {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }

        payload = {
            'message': message,
            'agent_uuid': teammate_id,
            'session_id': os.environ.get('KUBIYA_SESSION_ID', '')
        }

        try:
            response = requests.post(
                f"{self.base_url}/converse",
                headers=headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()

            # Process SSE response
            last_message = None
            for line in response.iter_lines():
                if line:
                    try:
                        event = json.loads(line)
                        if event.get('message'):
                            last_message = event['message']
                            if event.get('done', False):
                                break
                    except json.JSONDecodeError:
                        continue

            return {'response': last_message} if last_message else {'error': 'No response received'}

        except requests.RequestException as e:
            logger.error(f"Failed to send message: {str(e)}")
            return {'error': str(e)} 